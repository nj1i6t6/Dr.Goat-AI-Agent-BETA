from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils import call_gemini_api, get_sheep_info_for_context, encode_image_to_base64
from app.models import db, ChatHistory
from app.schemas import (
    AgentRecommendationModel,
    AgentChatModel,
    AnalyticsReportRequestModel,
    create_error_response,
)
from app.rag_loader import get_status as get_rag_status, rag_query
from pydantic import ValidationError
from datetime import datetime
from html import escape as html_escape
from html.parser import HTMLParser
import markdown
import base64
import bleach
from bleach.linkifier import Linker

bp = Blueprint('agent', __name__)

_RECOMMENDATION_FIELD_LABELS = {
    'EarNum': '耳號',
    'Breed': '品種',
    'Body_Weight_kg': '體重 (kg)',
    'Age_Months': '月齡 (月)',
    'Sex': '性別',
    'status': '生理狀態',
    'target_average_daily_gain_g': '目標日增重 (g/天)',
    'milk_yield_kg_day': '日產奶量 (kg/天)',
    'milk_fat_percentage': '乳脂率 (%)',
    'number_of_fetuses': '懷胎數',
    'activity_level': '活動量',
    'primary_forage_type': '主要草料',
}

MAX_BREAKDOWN_ITEMS_FOR_PROMPT = 6

_ALLOWED_RICH_TEXT_TAGS = {
    'a',
    'p',
    'br',
    'strong',
    'em',
    'ul',
    'ol',
    'li',
    'code',
    'pre',
    'blockquote',
    'table',
    'thead',
    'tbody',
    'tr',
    'th',
    'td',
    'hr',
    'span',
    'div',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
}

_ALLOWED_RICH_TEXT_ATTRS = {
    'a': ['href', 'title', 'rel', 'target'],
}

_ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
_REQUIRED_LINK_REL = ('noopener', 'noreferrer', 'nofollow')


def _secure_link_callback(attrs: dict[str, str], new: bool = False) -> dict[str, str]:
    href = attrs.get('href')
    if not href:
        return attrs

    attrs['target'] = '_blank'
    rel_values = set(token for token in attrs.get('rel', '').split() if token)
    rel_values.update({'noopener', 'noreferrer', 'nofollow'})
    attrs['rel'] = ' '.join(sorted(rel_values))
    return attrs


_RICH_TEXT_LINKER = Linker(callbacks=[_secure_link_callback], skip_tags=['code', 'pre'])


class _AnchorAttributeEnforcer(HTMLParser):
    """Post-sanitisation HTML parser that enforces secure anchor attributes."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        self._parts.append(self._render_start(tag, attrs, self_closing=False))

    def handle_startendtag(self, tag: str, attrs):
        self._parts.append(self._render_start(tag, attrs, self_closing=True))

    def handle_endtag(self, tag: str):
        self._parts.append(f"</{tag}>")

    def handle_data(self, data: str):
        self._parts.append(data)

    def handle_entityref(self, name: str):
        self._parts.append(f"&{name};")

    def handle_charref(self, name: str):
        self._parts.append(f"&#{name};")

    def handle_comment(self, data: str):
        self._parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str):
        self._parts.append(f"<!{decl}>")

    def unknown_decl(self, data: str):  # pragma: no cover - defensive
        self._parts.append(f"<![{data}]>")

    def get_html(self) -> str:
        return ''.join(self._parts)

    def _render_start(self, tag: str, attrs, *, self_closing: bool) -> str:
        attributes = self._normalise_attrs(tag, attrs)
        rendered = ''.join(self._render_attr(name, value) for name, value in attributes.items())
        closing = ' /' if self_closing else ''
        return f"<{tag}{rendered}{closing}>"

    def _normalise_attrs(self, tag: str, attrs) -> dict[str, str | None]:
        attr_map: dict[str, str | None] = {}
        for name, value in attrs:
            attr_map[name] = value

        if tag.lower() == 'a':
            rel_tokens = {
                token.lower()
                for token in (attr_map.get('rel') or '').split()
                if token
            }
            rel_tokens.update(_REQUIRED_LINK_REL)
            ordered_rel = ' '.join(token for token in _REQUIRED_LINK_REL if token in rel_tokens)
            attr_map['rel'] = ordered_rel

            href = attr_map.get('href') or ''
            if href:
                attr_map['target'] = attr_map.get('target') or '_blank'
            else:
                attr_map.pop('target', None)

        return attr_map

    @staticmethod
    def _render_attr(name: str, value: str | None) -> str:
        if value is None:
            return f" {name}"
        return f" {name}=\"{html_escape(value, quote=True)}\""


def _enforce_anchor_security(html: str) -> str:
    parser = _AnchorAttributeEnforcer()
    parser.feed(html)
    parser.close()
    return parser.get_html()


def _sanitize_rich_text(html: str) -> str:
    if not html:
        return ''

    clean_html = bleach.clean(
        html,
        tags=_ALLOWED_RICH_TEXT_TAGS,
        attributes=_ALLOWED_RICH_TEXT_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
    linked_html = _RICH_TEXT_LINKER.linkify(clean_html)
    return _enforce_anchor_security(linked_html)


def _format_rag_context(chunks: list[dict[str, object]]) -> str:
    if not chunks:
        return ""

    lines = ["\n--- 參考知識庫片段 ---"]
    for idx, chunk in enumerate(chunks, 1):
        source = chunk.get('doc', 'unknown')
        chunk_idx = chunk.get('idx', 'N/A')
        score = chunk.get('score', 0.0)
        lines.append(
            f"[{idx}] 來源: {source} (段落 {chunk_idx}, 相似度 {score:.2f})\n{chunk.get('text', '').strip()}"
        )
    lines.append("--- 參考片段結束 ---\n")
    return "\n".join(lines)


def _build_recommendation_rag_query(data: dict, sheep_context: str) -> str:
    query_lines = []
    for key, label in _RECOMMENDATION_FIELD_LABELS.items():
        value = data.get(key)
        if value not in (None, ""):
            query_lines.append(f"{label}: {value}")

    other_notes = data.get('other_remarks')
    if other_notes:
        query_lines.append(f"其他備註: {other_notes}")

    if sheep_context:
        query_lines.append(sheep_context.strip())

    return "\n".join(query_lines)

@bp.route('/tip', methods=['GET'])
@login_required
def get_agent_tip():
    """獲取每日提示"""
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return jsonify(error="未提供API金鑰於請求頭中 (X-Api-Key)"), 401
    
    current_month = datetime.now().month
    season = "夏季"
    if 3 <= current_month <= 5: season = "春季"
    elif 9 <= current_month <= 11: season = "秋季"
    elif current_month in [12, 1, 2]: season = "冬季"
    
    prompt = f"作為『領頭羊博士』，請給我一條關於台灣當前季節（{season}）的實用山羊飼養小提示，簡短且易懂，請使用 Markdown 格式，例如將重點字詞用 `**` 包裹起來。"

    result = call_gemini_api(prompt, api_key, generation_config_override={"temperature": 0.7})
    if "error" in result:
        return jsonify(error=result["error"]), 500
    
    tip_text = result.get("text", "保持羊舍通風乾燥，提供清潔飲水。")
    tip_html = markdown.markdown(tip_text, extensions=['nl2br', 'fenced_code', 'tables'])
    return jsonify(tip_html=_sanitize_rich_text(tip_html))


@bp.route('/status', methods=['GET'])
@login_required
def agent_status():
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return jsonify(error="未提供API金鑰於請求頭中 (X-Api-Key)"), 401

    status = get_rag_status()
    return jsonify(
        rag_enabled=bool(status.get('available')),  # type: ignore[arg-type]
        message=status.get('message', ''),
        detail=status.get('detail'),
    )


def _format_filters(filters: dict[str, object]) -> str:
    if not filters:
        return '（無額外篩選）'
    lines = []
    for key, value in filters.items():
        if value in (None, '', []):
            continue
        if isinstance(value, list):
            formatted = ', '.join(str(v) for v in value)
        else:
            formatted = str(value)
        lines.append(f"- {key}: {formatted}")
    return '\n'.join(lines) if lines else '（無額外篩選）'


def _format_cohort_rows(rows: list[dict[str, object]]) -> str:
    if not rows:
        return '尚未執行分群分析或沒有符合條件的羊群。'
    formatted_rows = []
    for row in rows:
        metrics = row.get('metrics', {})
        dims = {k: v for k, v in row.items() if k != 'metrics'}
        dim_text = ', '.join(f"{k}: {v}" for k, v in dims.items() if v not in (None, '')) or '未指定維度'
        metric_text = ', '.join(f"{k}={v}" for k, v in metrics.items() if v is not None) or '無指標資料'
        formatted_rows.append(f"• {dim_text} → {metric_text}")
    return '\n'.join(formatted_rows)


def _format_cost_benefit(summary: dict[str, object]) -> str:
    if not summary:
        return '尚未計算成本收益。'
    parts = []
    total_cost = summary.get('summary', {}).get('total_cost')
    total_revenue = summary.get('summary', {}).get('total_revenue')
    net_profit = summary.get('summary', {}).get('net_profit')
    if total_cost is not None:
        parts.append(f"總成本: {total_cost:,.2f}")
    if total_revenue is not None:
        parts.append(f"總收益: {total_revenue:,.2f}")
    if net_profit is not None:
        parts.append(f"淨收益: {net_profit:,.2f}")
    if not parts:
        parts.append('目前缺少成本收益資料。')

    breakdowns = []
    for item in summary.get('items', [])[:MAX_BREAKDOWN_ITEMS_FOR_PROMPT]:
        label = item.get('group', '未分組')
        metrics = item.get('metrics', {})
        metric_text = ', '.join(f"{k}={v}" for k, v in metrics.items() if v is not None)
        breakdowns.append(f"- {label}: {metric_text}")

    if breakdowns:
        parts.append('\n主要分組表現:\n' + '\n'.join(breakdowns))

    return '\n'.join(parts)


@bp.route('/analytics-report', methods=['POST'])
@login_required
def generate_analytics_report():
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return jsonify(create_error_response('未提供 API 金鑰', [{'loc': ['header', 'X-Api-Key'], 'msg': '必須包含 X-Api-Key'}])), 401

    try:
        payload = AnalyticsReportRequestModel(**(request.get_json() or {}))
    except ValidationError as exc:
        return jsonify(create_error_response('請求資料驗證失敗', exc.errors())), 400

    data = payload.model_dump()
    filters = _format_filters(data.get('filters', {}))
    cohort_summary = _format_cohort_rows(data.get('cohort', []))
    cost_benefit_summary = _format_cost_benefit(data.get('cost_benefit', {}))
    extra_insights = '\n'.join(f"- {note}" for note in data.get('insights', []) if note)
    if not extra_insights:
        extra_insights = '（目前尚未填寫其他觀察）'

    prompt = (
        "你是台灣畜牧產業的財務顧問，熟悉山羊飼養成本與收益。"
        "請根據以下數據輸出一份 300-400 字的繁體中文報告，包含 KPI 摘要、異常提醒、建議行動與後續追蹤指標。\n"
        "--- 篩選條件 ---\n"
        f"{filters}\n\n"
        "--- 分群分析 ---\n"
        f"{cohort_summary}\n\n"
        "--- 成本收益摘要 ---\n"
        f"{cost_benefit_summary}\n\n"
        "--- 使用者備註 ---\n"
        f"{extra_insights}\n\n"
        "請重點標示 ROI 最高與最低的分群，並提供可立即採取的改善建議。最後給出下週需追蹤的 2 項量化指標。"
    )

    result = call_gemini_api(prompt, api_key, generation_config_override={'temperature': 0.35})
    if 'error' in result:
        return jsonify(error=result['error']), 500

    report_text = result.get('text', '').strip()
    report_html = markdown.markdown(report_text, extensions=['fenced_code', 'tables', 'nl2br'])
    clean_report_html = _sanitize_rich_text(report_html)
    return jsonify(report_html=clean_report_html, report_markdown=report_text)

@bp.route('/recommendation', methods=['POST'])
@login_required
def get_recommendation():
    """獲取飼養建議"""
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return jsonify(create_error_response('未提供 API 金鑰', [{'loc': ['header', 'X-Api-Key'], 'msg': '必須包含 X-Api-Key'}])), 401

    try:
        # 使用 Pydantic 驗證請求資料
        recommendation_data = AgentRecommendationModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response("請求資料驗證失敗", e.errors())), 400

    # 將 Pydantic 模型轉換為字典
    data = recommendation_data.model_dump(exclude_unset=True)
    
    ear_num = data.get('EarNum')
    sheep_context_str = ""
    if ear_num:
        sheep_db_info = get_sheep_info_for_context(ear_num, current_user.id)
        if sheep_db_info:
            # 使用資料庫數據填充空值
            for key in ['Breed', 'Sex', 'BirthDate', 'agent_notes', 'activity_level', 'primary_forage_type']:
                if not data.get(key) and sheep_db_info.get(key):
                    data[key] = sheep_db_info.get(key)
            
            # 組合背景資料字串
            sheep_context_str += f"\n\n--- 關於耳號 {sheep_db_info['EarNum']} 的額外背景資料 ---\n"
            if sheep_db_info.get('agent_notes'): sheep_context_str += f"我的觀察筆記: {sheep_db_info['agent_notes']}\n"
            if sheep_db_info.get('primary_forage_type'): sheep_context_str += f"主要草料: {sheep_db_info['primary_forage_type']}\n"
            
            if sheep_db_info.get('history_records'):
                history_by_type = {}
                # 將紀錄按類型分組
                for rec in reversed(sheep_db_info['history_records']):
                    rec_type_str = rec.get('record_type')
                    if rec_type_str not in history_by_type:
                        history_by_type[rec_type_str] = []
                    history_by_type[rec_type_str].append(f"{rec['record_date']}({rec['value']})")
                
                sheep_context_str += "歷史數據趨勢:\n"
                for rec_type, values in history_by_type.items():
                    sheep_context_str += f"- {rec_type}: {', '.join(values)}\n"

            if sheep_db_info.get('recent_events'):
                sheep_context_str += "近期事件:\n"
                for event in sheep_db_info['recent_events']:
                    sheep_context_str += f"- {event['event_date']} {event['event_type']}: {event.get('description','無描述')}\n"

    # ESG Prompt 升級
    esg_prompt_instruction = (
        "\n--- ESG 永續性分析 ---\n"
        "除了上述營養建議，請務必增加一個「環境影響與動物福利」的分析區塊。在這個區塊中，請包含：\n"
        "1. **環境影響評估**：根據羊隻的體重和生理狀態，粗估其每日的甲烷排放量(g/day)。\n"
        "2. **低碳飼養建議**：推薦 1-2 種可行的低碳飼料替代方案或添加劑（例如，使用在地草料、海藻粉、單寧等），並簡要說明其減排潛力。\n"
        "3. **動物福利建議**：根據羊隻的生理狀態，提供 1-2 項能減少緊迫 (stress) 的具體管理建議（例如，飼養密度、環境豐富化等）。"
    )

    prompt_parts = [
        f"你是一位名叫『領頭羊博士』的AI羊隻飼養顧問，你非常了解台灣的氣候和常見飼養方式，並且嚴格遵循美國國家科學研究委員會 NRC (2007) 《Nutrient Requirements of Small Ruminants》的指南。你正在為耳號為 **{data.get('EarNum', '一隻未指定耳號')}** 的羊隻提供飼養營養建議。",
        "請根據以下提供的羊隻數據和背景資料，提供一份每日飼料營養需求的詳細建議，包括DMI, ME, CP, Ca, P, 鈣磷比，以及其他適用礦物質和維生素。並針對特定生理狀態給予台灣本土化操作建議。請用 Markdown 格式清晰呈現。\n",
        "--- 羊隻當前數據 ---"
    ]
    
    # 動態添加用戶輸入的數據
    for key, label in _RECOMMENDATION_FIELD_LABELS.items():
        if data.get(key):
            prompt_parts.append(f"- {label}: {data[key]}")

    full_prompt = "\n".join(prompt_parts) + sheep_context_str
    if data.get('other_remarks'):
        full_prompt += f"\n\n--- 使用者提供的其他備註 ---\n{data.get('other_remarks')}"

    rag_query_text = _build_recommendation_rag_query(data, sheep_context_str)
    rag_chunks = rag_query(rag_query_text, api_key=api_key)
    rag_context_text = _format_rag_context(rag_chunks)
    if rag_context_text:
        full_prompt = rag_context_text + "\n" + full_prompt

    full_prompt += esg_prompt_instruction
    full_prompt += "\n\n請開始提供您的綜合建議。"

    result = call_gemini_api(full_prompt, api_key)
    if "error" in result:
        return jsonify(error=result["error"]), 500
    
    recommendation_html = markdown.markdown(result.get("text",""), extensions=['fenced_code', 'tables', 'nl2br'])
    return jsonify(recommendation_html=recommendation_html)


@bp.route('/chat', methods=['POST'])
@login_required
def chat_with_agent():
    """與 AI 聊天，支援文字和圖片"""
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return jsonify(create_error_response('未提供 API 金鑰', [{'loc': ['header', 'X-Api-Key'], 'msg': '必須包含 X-Api-Key'}])), 401

    try:
        # 檢查是否為包含檔案的請求
        if 'image' in request.files:
            # 處理包含圖片的請求
            user_message = request.form.get('message', '')
            session_id = request.form.get('session_id')
            ear_num_context = request.form.get('ear_num_context')
            image_file = request.files['image']
            
            if not session_id:
                return jsonify(error="缺少必要參數"), 400
            
            # 驗證圖片
            if not image_file or not image_file.filename:
                return jsonify(error="未選擇圖片檔案"), 400
            
            # 檢查檔案類型
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return jsonify(error="不支援的圖片格式，請使用 JPEG、PNG、GIF 或 WebP"), 400
            
            # 檢查檔案大小 (10MB)
            image_data = image_file.read()
            if len(image_data) > 10 * 1024 * 1024:
                return jsonify(error="圖片檔案不能超過 10MB"), 400
            
            # 將圖片編碼為 base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
        else:
            # 處理純文字請求
            chat_data = AgentChatModel(**request.get_json())
            user_message = chat_data.message
            session_id = chat_data.session_id
            ear_num_context = chat_data.ear_num_context
            image_base64 = None
            
    except ValidationError as e:
        return jsonify(create_error_response("聊天資料驗證失敗", e.errors())), 400
    except Exception as e:
        return jsonify(error=f"處理請求時發生錯誤: {str(e)}"), 400

    # 獲取聊天歷史
    history = ChatHistory.query.filter_by(
        user_id=current_user.id, 
        session_id=session_id
    ).order_by(ChatHistory.timestamp.asc()).limit(20).all()
    
    # 建立對話歷史
    chat_messages_for_api = [
        {"role": "user", "parts": [{"text": "你是一位名叫『領頭羊博士』的AI羊隻飼養代理人，你非常了解台灣的氣候和常見飼養方式。請友善且專業地回答使用者的問題。當用戶上傳山羊照片時，請仔細分析照片中山羊的外觀、健康狀況、環境等，並給出專業的飼養建議。"}]},
        {"role": "model", "parts": [{"text": "是的，領頭羊博士在此為您服務。請問有什麼問題嗎？"}]}
    ]
    for entry in history:
        chat_messages_for_api.append({"role": entry.role, "parts": [{"text": entry.content}]})

    # 加入羊隻背景資料
    sheep_context_text = ""
    if ear_num_context:
        sheep_cxt = get_sheep_info_for_context(ear_num_context, current_user.id)
        if sheep_cxt:
            context_parts = [f"\n\n[背景資料] 我目前正在關注羊隻 {ear_num_context}。"]
            basic_info = {k: v for k, v in sheep_cxt.items() if k in ['Breed', 'Sex', 'BirthDate', 'status'] and v is not None}
            if basic_info:
                context_parts.append("牠的基本資料如下：")
                for key, value in basic_info.items():
                    context_parts.append(f"- {key}: {value}")
            
            if sheep_cxt.get('recent_events'):
                context_parts.append("\n牠最近的事件記錄：")
                for event in sheep_cxt['recent_events']:
                    context_parts.append(f"- {event['event_date']} {event['event_type']}: {event.get('description','無描述')}")
            
            sheep_context_text = "\n".join(context_parts)

    # 準備用戶訊息
    current_user_message_with_context = user_message + sheep_context_text

    rag_chunks = rag_query(user_message + sheep_context_text, api_key=api_key)
    rag_context_text = _format_rag_context(rag_chunks)
    if rag_context_text:
        current_user_message_with_context = rag_context_text + "\n" + current_user_message_with_context
    
    # 如果有圖片，加入圖片部分
    user_message_parts = [{"text": current_user_message_with_context}]
    if image_base64:
        mime_type = "image/jpeg"  # 默認值
        if 'image' in request.files:
            mime_type = image_file.content_type
        
        user_message_parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_base64
            }
        })
    
    chat_messages_for_api.append({"role": "user", "parts": user_message_parts})

    # 呼叫 Gemini API
    gemini_response = call_gemini_api(chat_messages_for_api, api_key, generation_config_override={"temperature": 0.7})

    if "error" in gemini_response:
        return jsonify(error=gemini_response['error']), 500

    model_reply_text = gemini_response.get("text", "抱歉，我暫時無法回答。")
    
    # 儲存聊天記錄
    try:
        # 為包含圖片的訊息添加標記
        user_content = user_message
        if image_base64:
            user_content += " [包含圖片]"
            
        user_entry = ChatHistory(user_id=current_user.id, session_id=session_id, role='user', content=user_content, ear_num_context=ear_num_context)
        model_entry = ChatHistory(user_id=current_user.id, session_id=session_id, role='model', content=model_reply_text, ear_num_context=ear_num_context)
        db.session.add(user_entry)
        db.session.add(model_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"儲存聊天記錄失败: {e}")

    reply_html = markdown.markdown(model_reply_text, extensions=['fenced_code', 'tables', 'nl2br'])
    return jsonify(reply_html=reply_html)
