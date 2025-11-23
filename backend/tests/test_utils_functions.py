"""
工具功能測試
測試 utils.py 中的功能函數
"""

from unittest.mock import MagicMock, patch

import pytest

from app.ai.genai_client import GenAIClientError, GenAIResponse, GenAIPromptBlocked
from app.utils import call_gemini_api, get_sheep_info_for_context


class TestUtilsFunctions:
    """工具功能測試類別"""

    @patch('app.utils.generate_content')
    def test_call_gemini_api_success(self, mock_generate):
        """測試成功調用 Gemini API"""

        mock_generate.return_value = GenAIResponse(
            text="這是一個關於羊隻管理的測試回應",
            finish_reason="STOP",
            raw_response=MagicMock(),
            candidate=MagicMock(),
        )

        result = call_gemini_api("如何照顧羊隻？", "test_api_key")

        assert result["text"] == "這是一個關於羊隻管理的測試回應"
        assert result["finish_reason"] == "STOP"
        mock_generate.assert_called_once()

    @patch('app.utils.generate_content')
    def test_call_gemini_api_with_list_prompt(self, mock_generate):
        """測試使用列表格式的提示詞"""

        mock_generate.return_value = GenAIResponse(
            text="回應列表格式的提示",
            finish_reason="STOP",
            raw_response=MagicMock(),
            candidate=MagicMock(),
        )

        prompt_text = [{"role": "user", "parts": [{"text": "測試問題"}]}]
        result = call_gemini_api(prompt_text, "test_api_key")

        assert result["text"] == "回應列表格式的提示"
        assert result["finish_reason"] == "STOP"

    @patch('app.utils.generate_content')
    def test_call_gemini_api_http_error(self, mock_generate):
        """測試 HTTP 錯誤處理"""

        mock_generate.side_effect = GenAIClientError("GenAI API error (code 400): API 金鑰無效")

        result = call_gemini_api("測試", "invalid_key")

        assert "error" in result
        assert "API 金鑰無效" in result["error"]

    @patch('app.utils.generate_content')
    def test_call_gemini_api_request_exception(self, mock_generate):
        """測試 SDK 異常轉換"""

        mock_generate.side_effect = GenAIClientError("網路或請求錯誤: timeout")

        result = call_gemini_api("測試", "test_key")

        assert "error" in result
        assert "網路或請求錯誤" in result["error"]

    @patch('app.utils.generate_content')
    def test_call_gemini_api_prompt_blocked(self, mock_generate):
        """測試提示詞被封鎖"""

        rating = MagicMock()
        rating.model_dump.return_value = {"category": "HARM_CATEGORY_HARASSMENT", "probability": "HIGH"}
        mock_generate.side_effect = GenAIPromptBlocked("SAFETY", [rating])

        result = call_gemini_api("不當內容", "test_key")

        assert "error" in result
        assert "提示詞被拒絕" in result["error"]
        assert "SAFETY" in result["error"]

    @patch('app.utils.generate_content')
    def test_call_gemini_api_unexpected_response(self, mock_generate):
        """測試意外的 API 回應格式"""

        mock_generate.side_effect = GenAIClientError("GenAI response did not contain any candidates.")

        result = call_gemini_api("測試", "test_key")

        assert "error" in result
        assert "candidates" in result["error"]

    @patch('app.utils.generate_content')
    def test_call_gemini_api_with_custom_config(self, mock_generate):
        """測試自訂配置參數"""

        captured_kwargs = {}

        def _fake_generate(prompt, **kwargs):
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            return GenAIResponse(
                text="自訂配置回應",
                finish_reason="STOP",
                raw_response=MagicMock(),
                candidate=MagicMock(),
            )

        mock_generate.side_effect = _fake_generate

        generation_config_override = {"temperature": 0.8}
        safety_settings_override = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"}]

        result = call_gemini_api("測試", "test_key", generation_config_override, safety_settings_override)

        assert result["text"] == "自訂配置回應"
        assert captured_kwargs["generation_config_override"] == generation_config_override
        assert captured_kwargs["safety_settings_override"] == safety_settings_override

    def test_get_sheep_info_for_context_no_ear_num(self):
        """測試沒有耳號的情況"""
        result = get_sheep_info_for_context("", 1)
        assert result is None
        
        result = get_sheep_info_for_context(None, 1)
        assert result is None

    def test_get_sheep_info_for_context_sheep_not_found(self, app):
        """測試找不到羊隻的情況"""
        with app.app_context():
            result = get_sheep_info_for_context("NONEXISTENT", 1)
            assert result is None

    def test_get_sheep_info_for_context_success(self, test_sheep, app):
        """測試成功獲取羊隻資訊"""
        with app.app_context():
            # 添加一些事件和歷史記錄
            from app.models import SheepEvent, SheepHistoricalData, db
            
            event = SheepEvent(
                user_id=1,
                sheep_id=test_sheep.id,
                event_date='2024-01-15',
                event_type='疫苗接種',
                description='接種測試疫苗'
            )
            db.session.add(event)
            
            history = SheepHistoricalData(
                user_id=1,
                sheep_id=test_sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.0
            )
            db.session.add(history)
            db.session.commit()
            
            result = get_sheep_info_for_context(test_sheep.EarNum, 1)
            
            assert result is not None
            assert result['EarNum'] == test_sheep.EarNum
            assert 'recent_events' in result
            assert 'history_records' in result
            assert len(result['recent_events']) >= 1
            assert len(result['history_records']) >= 1

    @patch('app.utils.generate_content')
    def test_call_gemini_api_general_exception(self, mock_generate, app):
        """測試一般異常處理"""

        mock_generate.side_effect = Exception("未知錯誤")

        with app.app_context():
            result = call_gemini_api("測試", "test_key")

        assert "error" in result
        assert "處理 API 請求時發生未知錯誤" in result["error"]

    @patch('app.utils.generate_content')
    def test_call_gemini_api_timeout(self, mock_generate):
        """測試超時處理"""

        mock_generate.side_effect = GenAIClientError("網路或請求錯誤: 請求超時")

        result = call_gemini_api("測試", "test_key")

        assert "error" in result
        assert "網路或請求錯誤" in result["error"]

    @patch('app.utils.generate_content')
    def test_call_gemini_api_empty_text_response(self, mock_generate):
        """測試空回應文本"""

        mock_generate.return_value = GenAIResponse(
            text="",
            finish_reason="STOP",
            raw_response=MagicMock(),
            candidate=MagicMock(),
        )

        result = call_gemini_api("測試", "test_key")

        assert result["text"] == ""
        assert result["finish_reason"] == "STOP"
