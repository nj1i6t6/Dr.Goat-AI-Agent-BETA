import pandas as pd
import json
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Sheep, SheepEvent, SheepHistoricalData, ChatHistory
from app.utils import call_gemini_api

bp = Blueprint('data_management', __name__)

MAX_AI_PREVIEW_ROWS = 5
MAX_AI_VALUE_LENGTH = 120

AI_SHEET_PURPOSES = {
    "ignore": {
        "title": "忽略此工作表",
        "description": "不匯入此工作表的任何資料。"
    },
    "basic_info": {
        "title": "羊隻基礎資料",
        "description": "建立或更新羊隻主檔資訊，例如耳號、品種、出生日期等。"
    },
    "kidding_record": {
        "title": "分娩記錄",
        "description": "記錄羊隻的分娩事件及仔羊資訊。"
    },
    "mating_record": {
        "title": "配種記錄",
        "description": "記錄母羊的配種事件與公羊資訊。"
    },
    "yean_record": {
        "title": "泌乳 / 乾乳記錄",
        "description": "追蹤泌乳週期內的重要節點，例如開始泌乳與乾乳日期。"
    },
    "weight_record": {
        "title": "體重記錄",
        "description": "追蹤羊隻的體重測量歷史。"
    },
    "milk_yield_record": {
        "title": "產乳量記錄",
        "description": "記錄每次測量的產乳量資訊。"
    },
    "milk_analysis_record": {
        "title": "乳成分分析記錄",
        "description": "記錄乳成分分析結果，例如乳脂率。"
    },
    "breed_mapping": {
        "title": "品種代碼對照表",
        "description": "將外部品種代碼轉換為系統內部名稱。"
    },
    "sex_mapping": {
        "title": "性別代碼對照表",
        "description": "將外部性別代碼轉換為系統內部名稱。"
    }
}

REQUIRED_COLUMNS_BY_PURPOSE = {
    "ignore": [],
    "basic_info": ["EarNum"],
    "kidding_record": ["EarNum", "YeanDate"],
    "mating_record": ["EarNum", "Mat_date"],
    "yean_record": ["EarNum", "YeanDate"],
    "weight_record": ["EarNum", "MeaDate", "Weight"],
    "milk_yield_record": ["EarNum", "MeaDate", "Milk"],
    "milk_analysis_record": ["EarNum", "MeaDate", "AMFat"],
    "breed_mapping": ["Code", "Name"],
    "sex_mapping": ["Code", "Name"]
}

ALLOWED_SHEET_PURPOSES = set(AI_SHEET_PURPOSES.keys())


def _truncate_value(value, *, max_length: int = MAX_AI_VALUE_LENGTH):
    if value is None:
        return None
    text = str(value).strip()
    if len(text) > max_length:
        return text[:max_length] + '…'
    return text


def _extract_excel_summary(file_bytes: bytes):
    sheets_summary = {}
    with pd.ExcelFile(BytesIO(file_bytes)) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            df = df.where(pd.notna(df), None)
            preview_rows = []
            if not df.empty:
                for record in df.head(MAX_AI_PREVIEW_ROWS).to_dict(orient='records'):
                    truncated = {str(k): _truncate_value(v) for k, v in record.items()}
                    preview_rows.append(truncated)
            sheets_summary[sheet_name] = {
                "columns": [str(col) for col in df.columns],
                "rows": int(len(df)),
                "preview": preview_rows
            }
    return sheets_summary


def _extract_json_from_text(text: str):
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith('```'):
        parts = cleaned.split('```')
        if len(parts) >= 3:
            cleaned = parts[1].strip()
        if cleaned.startswith('json'):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 嘗試修剪可能的尾端註解再解析一次
        try:
            return json.loads(cleaned.rstrip(';'))
        except json.JSONDecodeError:
            raise


def _validate_ai_mapping(ai_data, sheets_summary):
    errors = []
    warnings = []
    metadata = {}
    normalized = {"sheets": {}}

    if not isinstance(ai_data, dict):
        errors.append("AI 回傳結果不是有效的 JSON 物件。")
        return normalized, warnings, errors, metadata

    ai_sheets = ai_data.get("sheets")
    if not isinstance(ai_sheets, dict):
        errors.append("AI 回傳結果缺少 sheets 物件或格式錯誤。")
        return normalized, warnings, errors, metadata

    workbook_sheet_names = set(sheets_summary.keys())

    for sheet_name in workbook_sheet_names:
        suggestion = ai_sheets.get(sheet_name)
        if not isinstance(suggestion, dict):
            warnings.append(f"AI 未提供工作表「{sheet_name}」的有效建議，請手動設定。")
            normalized["sheets"][sheet_name] = {"purpose": "", "columns": {}}
            continue

        purpose = suggestion.get("purpose", "")
        purpose = purpose.strip() if isinstance(purpose, str) else ""

        if purpose and purpose not in ALLOWED_SHEET_PURPOSES:
            warnings.append(f"AI 為工作表「{sheet_name}」建議的用途「{purpose}」不在允許清單內，已保留空白，請手動調整。")
            purpose = ""

        columns_mapping = suggestion.get("columns", {})
        if not isinstance(columns_mapping, dict):
            warnings.append(f"AI 為工作表「{sheet_name}」提供的欄位映射不是物件格式，請手動設定。")
            columns_mapping = {}

        normalized_columns = {}
        sheet_columns = set(sheets_summary[sheet_name]["columns"])
        for system_field, user_column in columns_mapping.items():
            if not isinstance(system_field, str):
                continue
            if not isinstance(user_column, str) or not user_column.strip():
                continue
            user_column_stripped = user_column.strip()
            if user_column_stripped not in sheet_columns:
                warnings.append(f"AI 為工作表「{sheet_name}」建議的欄位「{user_column_stripped}」不存在於來源資料中，已忽略。")
                continue
            normalized_columns[system_field] = user_column_stripped

        normalized["sheets"][sheet_name] = {
            "purpose": purpose,
            "columns": normalized_columns
        }

        confidence = suggestion.get("confidence")
        notes = suggestion.get("notes")
        metadata_entry = {}
        if isinstance(confidence, (float, int, str)):
            try:
                metadata_entry["confidence"] = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                warnings.append(f"AI 為工作表「{sheet_name}」提供的信心值無法解析，已忽略。")
        if isinstance(notes, str) and notes.strip():
            metadata_entry["notes"] = notes.strip()
        if metadata_entry:
            metadata[sheet_name] = metadata_entry

        required_fields = REQUIRED_COLUMNS_BY_PURPOSE.get(purpose, []) if purpose else []
        missing_required = [field for field in required_fields if field not in normalized_columns]
        if missing_required:
            warnings.append(
                f"工作表「{sheet_name}」的用途「{purpose or '尚未設定'}」缺少必要欄位: {', '.join(missing_required)}。"
            )

    for extra_sheet in set(ai_sheets.keys()) - workbook_sheet_names:
        warnings.append(f"AI 回傳了不存在的工作表「{extra_sheet}」，已忽略。")

    ai_warnings = ai_data.get("warnings")
    if isinstance(ai_warnings, list):
        warnings.extend(str(msg) for msg in ai_warnings if msg)

    return normalized, warnings, errors, metadata

@bp.route('/export_excel', methods=['GET'])
@login_required
def export_excel():
    """將用戶所有數據匯出為 Excel 檔案"""
    try:
        user_id = current_user.id
        db_engine = db.engine 

        # 準備查詢
        sheep_query = Sheep.query.filter_by(user_id=user_id).order_by(Sheep.EarNum)
        events_query = SheepEvent.query.join(Sheep).filter(Sheep.user_id==user_id).order_by(Sheep.EarNum, SheepEvent.event_date.desc())
        history_query = SheepHistoricalData.query.join(Sheep).filter(Sheep.user_id==user_id).order_by(Sheep.EarNum, SheepHistoricalData.record_date)
        chat_query = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp)

        # 讀取到 Pandas DataFrame
        df_sheep = pd.read_sql(sheep_query.statement, db_engine) if sheep_query.first() else pd.DataFrame()
        df_events = pd.read_sql(events_query.statement, db_engine) if events_query.first() else pd.DataFrame()
        df_history = pd.read_sql(history_query.statement, db_engine) if history_query.first() else pd.DataFrame()
        df_chat = pd.read_sql(chat_query.statement, db_engine) if chat_query.first() else pd.DataFrame()

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 確保至少有一個工作表
            has_data = False
            
            if not df_sheep.empty:
                df_sheep.to_excel(writer, sheet_name='Sheep_Basic_Info', index=False)
                has_data = True
            
            if not df_events.empty:
                # 建立羊隻 ID 到耳號的映射
                sheep_map = {s.id: s.EarNum for s in sheep_query.all()}
                df_events['EarNum'] = df_events['sheep_id'].map(sheep_map)
                # 重新排列欄位，將 EarNum 放在最前面
                cols = ['EarNum'] + [col for col in df_events.columns if col not in ['EarNum', 'sheep_id']]
                df_events[cols].to_excel(writer, sheet_name='Sheep_Events_Log', index=False)
                has_data = True

            if not df_history.empty:
                if 'sheep_map' not in locals():
                    sheep_map = {s.id: s.EarNum for s in sheep_query.all()}
                df_history['EarNum'] = df_history['sheep_id'].map(sheep_map)
                cols = ['EarNum'] + [col for col in df_history.columns if col not in ['EarNum', 'sheep_id']]
                df_history[cols].to_excel(writer, sheet_name='Sheep_Historical_Data', index=False)
                has_data = True
            
            if not df_chat.empty:
                df_chat.to_excel(writer, sheet_name='Chat_History', index=False)
                has_data = True
            
            # 如果沒有任何數據，創建一個空的工作表
            if not has_data:
                empty_df = pd.DataFrame({'說明': ['目前沒有數據可匯出']})
                empty_df.to_excel(writer, sheet_name='Empty_Export', index=False)

        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"goat_data_export_{timestamp}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        current_app.logger.error(f"匯出 Excel 失敗: {e}", exc_info=True)
        return jsonify(error=f"匯出 Excel 失敗: {str(e)}"), 500

@bp.route('/analyze_excel', methods=['POST'])
@login_required
def analyze_excel():
    """分析上傳的 Excel 檔案結構"""
    if 'file' not in request.files:
        return jsonify(error="沒有檔案被上傳"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="沒有選擇檔案"), 400
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        return jsonify(error="不支援的檔案格式，請上傳 .xlsx 或 .xls 檔案"), 400
        
    try:
        xls = pd.ExcelFile(file)
        sheets_data = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            df = df.where(pd.notna(df), None) # 將 NaN 轉換為 None
            preview_data = df.head(3).to_dict(orient='records')
            sheets_data[sheet_name] = {
                "columns": list(df.columns),
                "rows": len(df),
                "preview": preview_data
            }
        return jsonify(success=True, sheets=sheets_data)

    except Exception as e:
        current_app.logger.error(f"分析 Excel 檔案失敗: {e}", exc_info=True)
        return jsonify(error=f"分析 Excel 檔案失敗: {str(e)}"), 500


@bp.route('/ai_import_mapping', methods=['POST'])
@login_required
def ai_import_mapping():
    """使用 AI 分析 Excel 檔案並生成映射建議"""
    if 'file' not in request.files:
        return jsonify(error="沒有檔案被上傳"), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(error="沒有選擇檔案"), 400
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        return jsonify(error="不支援的檔案格式，請上傳 .xlsx 或 .xls 檔案"), 400

    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        api_key = current_app.config.get('GOOGLE_API_KEY')

    if not api_key:
        return jsonify(error="請先在系統設定頁面儲存您的 Gemini API 金鑰後再試一次。"), 401

    try:
        file.stream.seek(0)
        file_bytes = file.read()
        if not file_bytes:
            return jsonify(error="檔案內容為空，無法進行分析"), 400

        sheets_summary = _extract_excel_summary(file_bytes)
        if not sheets_summary:
            return jsonify(error="無法從檔案中讀取任何工作表，請確認檔案內容"), 400

        analysis_payload = {
            "file_name": file.filename,
            "sheet_count": len(sheets_summary),
            "sheets": sheets_summary
        }

        prompt_context = {
            "file_name": file.filename,
            "sheet_count": len(sheets_summary),
            "sheets": [
                {
                    "sheet_name": sheet_name,
                    "column_headers": details["columns"],
                    "row_count": details["rows"],
                    "sample_rows": details["preview"]
                }
                for sheet_name, details in sheets_summary.items()
            ]
        }

        system_fields_ground_truth = "### 系統欄位ID規則 (System Field ID Rules)\n"
        for purpose, fields in REQUIRED_COLUMNS_BY_PURPOSE.items():
            if fields:
                system_fields_ground_truth += (
                    f"- 當用途(purpose)為 '{purpose}' 時，你在 JSON 的 columns 物件中，只能使用以下這些字串作為 KEY： "
                    f"{json.dumps(fields, ensure_ascii=False)}\n"
                )
        system_fields_ground_truth = system_fields_ground_truth.strip()

        prompt = (
            "你是一位嚴謹的資料分析師，你的任務是協助『領頭羊博士』系統將使用者提供的 Excel 工作表映射到正確的資料結構。\n\n"
            f"{system_fields_ground_truth}\n\n"
            "### 系統允許的工作表用途 (Sheet Purposes)\n"
            f"{json.dumps(AI_SHEET_PURPOSES, ensure_ascii=False, indent=2)}\n\n"
            "### 任務說明\n"
            "1. 針對每一個工作表，判斷最合適的用途 (purpose)。\n"
            "2. 建立欄位映射 (columns)。這是最關鍵的工作：\n"
            "   - columns 物件的 KEY 必須完全取自上方欄位規則內對應用途允許的欄位名稱。\n"
            "   - columns 物件的 VALUE 必須精準對應使用者 Excel 的欄位名稱 (必須出現在 column_headers 清單內，且大小寫與空白需完全一致)。\n"
            "   - 絕對禁止自行杜撰、翻譯或改寫任何 KEY 或 VALUE。若找不到合適欄位，請將 VALUE 設為 null。\n"
            "3. 若無法判定用途，purpose 請填入空字串 \"\"；若確認應忽略，purpose 設為 \"ignore\"。\n"
            "4. 如果工作表缺少匯入所需的關鍵欄位，請在 notes 欄位清楚說明問題。\n"
            "5. confidence 值請使用 0 到 1 之間的小數 (越接近 1 表示越有把握)。\n"
            "6. 可選地提供 warnings (陣列) 及 global_notes (陣列) 來補充跨工作表的提醒。\n\n"
            "### 輸出格式要求\n"
            "- 僅能回傳純 JSON 字串，不得加入 Markdown、程式碼區塊或額外說明。\n"
            "- JSON 結構需符合下列樣式，未列出的欄位請勿新增：\n"
            "{\n"
            "  \"sheets\": {\n"
            "    \"工作表名稱\": {\n"
            "      \"purpose\": \"basic_info\",\n"
            "      \"confidence\": 0.85,\n"
            "      \"columns\": {\n"
            "        \"EarNum\": \"耳號欄位名稱\",\n"
            "        \"Breed\": \"品種欄位名稱\"\n"
            "      },\n"
            "      \"notes\": \"若有需要向使用者提醒事項，請在此補充。\"\n"
            "    }\n"
            "  },\n"
            "  \"warnings\": [\"若有跨工作表的提醒，可放在此處\"],\n"
            "  \"summary\": \"以 1-2 句話概述你對整體映射的觀察。\",\n"
            "  \"global_notes\": [\"可選的全域提醒。\"]\n"
            "}\n\n"
            "### 使用者 Excel 檔案結構摘要\n"
            f"{json.dumps(prompt_context, ensure_ascii=False, indent=2)}\n\n"
            "請遵循上述規則，僅輸出 JSON。"
        )

        ai_response = call_gemini_api(
            prompt,
            api_key,
            generation_config_override={"temperature": 0.25, "topK": 1, "topP": 0.9}
        )

        if not isinstance(ai_response, dict):
            return jsonify(error="AI 回傳格式異常，請稍後再試"), 502
        if "error" in ai_response:
            return jsonify(error=f"AI 分析失敗: {ai_response['error']}"), 502

        ai_text = ai_response.get("text", "")
        if not ai_text.strip():
            return jsonify(error="AI 未回傳任何內容，請稍後再試"), 502

        try:
            ai_data = _extract_json_from_text(ai_text)
        except json.JSONDecodeError as decode_error:
            current_app.logger.warning(
                "AI 回傳無法解析為 JSON，錯誤: %s，內容片段: %s",
                decode_error,
                ai_text[:500]
            )
            return jsonify(error="AI 回傳的資料格式不正確，請改用自訂導入或稍後再試"), 502

        mapping_config, warnings, errors, metadata = _validate_ai_mapping(ai_data, sheets_summary)
        if errors:
            return jsonify(error="AI 建議內容不完整: " + "；".join(errors)), 502

        summary_text = ai_data.get("summary") if isinstance(ai_data.get("summary"), str) else None
        global_notes = ai_data.get("global_notes") if isinstance(ai_data.get("global_notes"), list) else None

        response_payload = {
            "success": True,
            "analysis": analysis_payload,
            "mapping_config": mapping_config,
            "metadata": metadata,
            "warnings": warnings
        }
        if summary_text:
            response_payload["summary"] = summary_text.strip()
        if global_notes:
            response_payload["ai_notes"] = [str(note) for note in global_notes if note]

        return jsonify(response_payload)

    except Exception as e:
        current_app.logger.error(f"AI 智慧導入分析失敗: {e}", exc_info=True)
        return jsonify(error=f"AI 智慧分析過程中發生錯誤: {str(e)}"), 500

@bp.route('/process_import', methods=['POST'])
@login_required
def process_import():
    """處理數據導入"""
    if 'file' not in request.files:
        return jsonify(error="請求缺少檔案參數"), 400
    
    file = request.files['file']
    is_default_mode = request.form.get('is_default_mode', 'false').lower() == 'true'

    if is_default_mode:
        # 內建的標準範本映射設定
        config = {
            "sheets": {
                "0009-0013A1_Basic": {"purpose": "basic_info", "columns": {"EarNum": "EarNum", "Breed": "Breed", "Sex": "Sex", "BirthDate": "BirthDate", "Sire": "Sire", "Dam": "Dam", "BirWei": "BirWei", "SireBre": "SireBre", "DamBre": "DamBre", "MoveCau": "MoveCau", "MoveDate": "MoveDate", "Class": "Class", "LittleSize": "LittleSize", "Lactation": "Lactation", "ManaClas": "ManaClas", "FarmNum": "FarmNum", "RUni": "RUni"}},
                "0009-0013A4_Kidding": {"purpose": "kidding_record", "columns": {"EarNum": "EarNum", "YeanDate": "YeanDate", "KidNum": "KidNum", "KidSex": "KidSex"}},
                "0009-0013A2_PubMat": {"purpose": "mating_record", "columns": {"EarNum": "EarNum", "Mat_date": "Mat_date", "Mat_grouM_Sire": "Mat_grouM_Sire"}},
                "0009-0013A3_Yean": {"purpose": "yean_record", "columns": {"EarNum": "EarNum", "YeanDate": "YeanDate", "DryOffDate": "DryOffDate", "Lactation": "Lactation"}},
                "0009-0013A9_Milk": {"purpose": "milk_yield_record", "columns": {"EarNum": "EarNum", "MeaDate": "MeaDate", "Milk": "Milk"}},
                "0009-0013A11_MilkAnalysis": {"purpose": "milk_analysis_record", "columns": {"EarNum": "EarNum", "MeaDate": "MeaDate", "AMFat": "AMFat"}},
                "S2_Breed": {"purpose": "breed_mapping", "columns": {"Code": "Symbol", "Name": "Breed"}},
                "S7_Sex": {"purpose": "sex_mapping", "columns": {"Code": "Num", "Name": "Sex"}},
            }
        }
    else:
        if 'mapping_config' not in request.form:
            return jsonify(error="手動模式請求缺少映射設定參數"), 400
        try:
            config = json.loads(request.form['mapping_config'])
        except json.JSONDecodeError:
            return jsonify(error="映射設定格式錯誤"), 400

    try:
        xls = pd.ExcelFile(file)
        report_details = []
        
        def format_date(d):
            if pd.isna(d) or d is None: return None
            try:
                # 處理 '1900-01-01' 或 '1900/1/1' 這類代表空值的日期
                if '1900' in str(d): return None
                dt = pd.to_datetime(d)
                # 處理 excel 日期原點問題
                if dt.year < 1901: return None
                return dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                return None

        # --- 第一階段：讀取映射表並建立羊隻基礎資料 ---
        breed_map, sex_map = {}, {}
        sheets_to_process = config.get('sheets', {})

        # 優先處理映射表
        for sheet_name, sheet_config in sheets_to_process.items():
            if sheet_name not in xls.sheet_names: continue
            purpose = sheet_config.get('purpose')
            cols = sheet_config.get('columns', {})
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str).where(pd.notna, None)
            
            if purpose == 'breed_mapping' and cols.get('Code') and cols.get('Name'):
                for _, row in df.iterrows():
                    if row.get(cols['Code']): breed_map[str(row[cols['Code']])] = row[cols['Name']]
            elif purpose == 'sex_mapping' and cols.get('Code') and cols.get('Name'):
                for _, row in df.iterrows():
                    if row.get(cols['Code']): sex_map[str(row[cols['Code']])] = row[cols['Name']]

        # 處理基礎資料
        for sheet_name, sheet_config in sheets_to_process.items():
            if sheet_name not in xls.sheet_names or sheet_config.get('purpose') != 'basic_info': continue
            
            cols = sheet_config.get('columns', {})
            if 'EarNum' not in cols: continue
            
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str).where(pd.notna, None)
            created, updated = 0, 0
            for _, row in df.iterrows():
                ear_num = row.get(cols['EarNum'])
                if not ear_num: continue

                sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first()
                if not sheep:
                    sheep = Sheep(user_id=current_user.id, EarNum=ear_num)
                    db.session.add(sheep)
                    created += 1
                else:
                    updated += 1
                
                for db_field, xls_col in cols.items():
                    if hasattr(sheep, db_field) and xls_col in row and row[xls_col] is not None:
                        value = row[xls_col]
                        if db_field == 'Breed': value = breed_map.get(str(value), value)
                        elif db_field == 'Sex': value = sex_map.get(str(value), value)
                        elif 'Date' in db_field: value = format_date(value)
                        setattr(sheep, db_field, value)
            
            db.session.commit() # 提交基礎資料變更
            report_details.append({"sheet": sheet_name, "message": f"處理完成。新增 {created} 筆，更新 {updated} 筆基礎資料。"})

        # --- 第二階段：處理事件和歷史數據 ---
        sheep_id_cache = {s.EarNum: s.id for s in Sheep.query.filter_by(user_id=current_user.id).all()}
        
        for sheet_name, sheet_config in sheets_to_process.items():
            if sheet_name not in xls.sheet_names or sheet_config.get('purpose') in ['ignore', 'basic_info', 'breed_mapping', 'sex_mapping']: continue

            cols = sheet_config.get('columns', {})
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str).where(pd.notna, None)
            count = 0
            
            for _, row in df.iterrows():
                ear_num = row.get(cols.get('EarNum'))
                sheep_id = sheep_id_cache.get(ear_num)
                if not sheep_id: continue
                
                # 初始化事件和歷史數據變數
                event_type, event_desc, event_date_val = None, None, None
                hist_type, hist_value, hist_date_val = None, None, None

                purpose = sheet_config.get('purpose')
                
                # 根據用途設定事件或歷史數據
                if purpose == 'kidding_record':
                    event_type, event_date_val = '產仔', row.get(cols.get('YeanDate'))
                    event_desc = f"產下仔羊: {row.get(cols.get('KidNum'))}" if cols.get('KidNum') in row else None
                
                elif purpose == 'mating_record':
                    event_type, event_date_val = '配種', row.get(cols.get('Mat_date'))
                    event_desc = f"配種公羊: {row.get(cols.get('Mat_grouM_Sire'))}" if cols.get('Mat_grouM_Sire') in row else None
                
                elif purpose == 'yean_record':
                    yean_date = format_date(row.get(cols.get('YeanDate')))
                    dry_off_date = format_date(row.get(cols.get('DryOffDate')))
                    lactation = row.get(cols.get('Lactation'))
                    if yean_date:
                        db.session.add(SheepEvent(user_id=current_user.id, sheep_id=sheep_id, event_date=yean_date, event_type='泌乳開始', description=f"第 {lactation} 胎次"))
                        count += 1
                    if dry_off_date:
                        db.session.add(SheepEvent(user_id=current_user.id, sheep_id=sheep_id, event_date=dry_off_date, event_type='乾乳', description=f"第 {lactation} 胎次結束"))
                        count += 1
                    continue
                
                elif purpose in ['weight_record', 'milk_yield_record', 'milk_analysis_record']:
                    if purpose == 'weight_record':
                        hist_type, hist_date_val, hist_value = 'Body_Weight_kg', row.get(cols.get('MeaDate')), row.get(cols.get('Weight'))
                    elif purpose == 'milk_yield_record':
                        hist_type, hist_date_val, hist_value = 'milk_yield_kg_day', row.get(cols.get('MeaDate')), row.get(cols.get('Milk'))
                    elif purpose == 'milk_analysis_record':
                        hist_type, hist_date_val, hist_value = 'milk_fat_percentage', row.get(cols.get('MeaDate')), row.get(cols.get('AMFat'))
                
                # 統一處理日期和數據寫入
                formatted_date = format_date(event_date_val or hist_date_val)
                if not formatted_date: continue

                if event_type:
                    db.session.add(SheepEvent(user_id=current_user.id, sheep_id=sheep_id, event_date=formatted_date, event_type=event_type, description=event_desc))
                    count += 1
                elif hist_type and hist_value is not None:
                    try:
                        db.session.add(SheepHistoricalData(user_id=current_user.id, sheep_id=sheep_id, record_date=formatted_date, record_type=hist_type, value=float(hist_value)))
                        count += 1
                    except (ValueError, TypeError):
                        continue

            if count > 0:
                report_details.append({"sheet": sheet_name, "message": f"成功導入 {count} 筆記錄。"})

        db.session.commit()
        return jsonify(success=True, message="數據導入已成功完成！", details=report_details)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"導入 Excel 數據失敗: {e}", exc_info=True)
        return jsonify(error=f"導入數據過程中發生錯誤: {str(e)}"), 500