import base64
from datetime import date, datetime
from typing import Any

from flask import current_app

from .models import Sheep, SheepEvent, SheepHistoricalData
from .ai.genai_client import (
    GenAIClientError,
    GenAIPromptBlocked,
    GenAIResponse,
    generate_content,
)


def normalise_json_payload(value: Any) -> Any:
    """Normalise nested structures for deterministic JSON serialisation."""

    if isinstance(value, datetime):
        return value.isoformat(timespec="microseconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [normalise_json_payload(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalise_json_payload(val) for key, val in value.items()}
    return value

def call_gemini_api(prompt_text, api_key, generation_config_override=None, safety_settings_override=None):
    """通用 Gemini API 調用函數 (基於 google-genai SDK)。"""

    try:
        response: GenAIResponse = generate_content(
            prompt_text,
            api_key=api_key,
            generation_config_override=generation_config_override,
            safety_settings_override=safety_settings_override,
        )
        finish_reason = response.finish_reason or "UNKNOWN"
        return {"text": response.text, "finish_reason": finish_reason}
    except GenAIPromptBlocked as exc:
        ratings = [rating.model_dump(mode="json") for rating in exc.safety_ratings]
        return {
            "error": f"提示詞被拒絕。原因：{exc.block_reason}。安全評級: {ratings}",
        }
    except GenAIClientError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.error("處理 API 請求時發生未知錯誤", exc_info=True)
        return {"error": f"處理 API 請求時發生未知錯誤: {exc}"}


def get_sheep_info_for_context(ear_num, user_id):
    """
    獲取指定羊隻的資訊，用於組合AI提示詞。
    """
    if not ear_num: return None
    
    sheep_info = Sheep.query.filter_by(EarNum=ear_num, user_id=user_id).first()
    if not sheep_info: return None
    
    sheep_dict = sheep_info.to_dict()
    
    # 獲取最近的5條事件記錄
    recent_events = SheepEvent.query.filter_by(sheep_id=sheep_info.id)\
        .order_by(SheepEvent.event_date.desc(), SheepEvent.id.desc())\
        .limit(5).all()
    sheep_dict['recent_events'] = [event.to_dict() for event in recent_events]
    
    # 獲取最近的10條歷史數據
    history_records = SheepHistoricalData.query.filter_by(
        sheep_id=sheep_info.id, user_id=user_id
    ).order_by(SheepHistoricalData.record_date.desc()).limit(10).all()
    sheep_dict['history_records'] = [rec.to_dict() for rec in history_records]

    return sheep_dict


def encode_image_to_base64(image_data):
    """
    將圖片數據編碼為 base64 字符串
    """
    return base64.b64encode(image_data).decode('utf-8')
