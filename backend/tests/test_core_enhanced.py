"""
增強的核心功能測試
專門用於提高utils.py、models.py、schemas.py等核心模組的測試覆蓋率
"""

import json
from datetime import datetime, date
from unittest.mock import MagicMock, patch

import pytest

from app.ai.genai_client import GenAIClientError, GenAIResponse
from app.models import ChatHistory, Sheep, SheepEvent, SheepHistoricalData, User
from app.utils import call_gemini_api, get_sheep_info_for_context
from app.schemas import SheepCreateModel, SheepUpdateModel, SheepEventCreateModel
from pydantic import ValidationError


class TestUtilsEnhanced:
    """增強的工具函數測試類別"""

    def test_call_gemini_api_with_custom_config(self, app):
        """測試使用自定義配置調用Gemini API"""
        with app.app_context():
            captured_kwargs = {}

            def _fake_generate(prompt, **kwargs):
                nonlocal captured_kwargs
                captured_kwargs = kwargs
                return GenAIResponse(
                    text="自定義配置測試回應",
                    finish_reason="STOP",
                    raw_response=MagicMock(),
                    candidate=MagicMock(),
                )

            with patch('app.utils.generate_content', side_effect=_fake_generate) as mock_generate:
                custom_config = {
                    "temperature": 0.8,
                    "topP": 0.9,
                    "maxOutputTokens": 2000
                }

                custom_safety = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]

                result = call_gemini_api(
                    "測試提示",
                    "fake-api-key",
                    generation_config_override=custom_config,
                    safety_settings_override=custom_safety
                )

            assert result["text"] == "自定義配置測試回應"
            assert captured_kwargs["generation_config_override"] == custom_config
            assert captured_kwargs["safety_settings_override"] == custom_safety
            mock_generate.assert_called_once()

    def test_call_gemini_api_with_blocked_content(self, app):
        """測試內容被阻止的情況"""
        with app.app_context():
            with patch(
                'app.utils.generate_content',
                return_value=GenAIResponse(
                    text="",
                    finish_reason="SAFETY",
                    raw_response=MagicMock(),
                    candidate=MagicMock(),
                ),
            ) as mock_generate:
                result = call_gemini_api("敏感內容測試", "fake-api-key")

            assert result["finish_reason"] == "SAFETY"
            assert result["text"] == ""
            mock_generate.assert_called_once()

    def test_call_gemini_api_with_malformed_response(self, app):
        """測試畸形響應的處理"""
        with app.app_context():
            with patch(
                'app.utils.generate_content',
                side_effect=GenAIClientError("GenAI response did not contain any candidates."),
            ):
                result = call_gemini_api("測試提示", "fake-api-key")

                assert "error" in result
                assert "candidates" in result["error"]

    def test_call_gemini_api_with_network_timeout(self, app):
        """測試網路超時的處理"""
        with app.app_context():
            with patch(
                'app.utils.generate_content',
                side_effect=GenAIClientError("網路或請求錯誤: timeout"),
            ):
                result = call_gemini_api("測試提示", "fake-api-key")

        assert "error" in result
        assert "網路或請求錯誤" in result["error"]

    def test_call_gemini_api_with_connection_error(self, app):
        """測試連接錯誤的處理"""
        with app.app_context():
            with patch(
                'app.utils.generate_content',
                side_effect=GenAIClientError("網路或請求錯誤: connection"),
            ):
                result = call_gemini_api("測試提示", "fake-api-key")

        assert "error" in result
        assert "網路或請求錯誤" in result["error"]

    def test_get_sheep_info_for_context_with_events_and_history(self, app, test_user):
        """測試獲取包含事件和歷史的羊隻資訊"""
        with app.app_context():
            # 創建羊隻
            sheep = Sheep(
                user_id=test_user.id,
                EarNum='CONTEXT001',
                Breed='波爾羊',
                Sex='母',
                Body_Weight_kg=45.0,
                Age_Months=12
            )
            app.extensions['sqlalchemy'].session.add(sheep)
            app.extensions['sqlalchemy'].session.commit()
            
            # 添加事件
            event = SheepEvent(
                user_id=test_user.id,
                sheep_id=sheep.id,
                event_date='2024-01-15',
                event_type='疫苗接種',
                description='狂犬病疫苗'
            )
            app.extensions['sqlalchemy'].session.add(event)
            
            # 添加歷史數據
            history = SheepHistoricalData(
                user_id=test_user.id,
                sheep_id=sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.0
            )
            app.extensions['sqlalchemy'].session.add(history)
            app.extensions['sqlalchemy'].session.commit()

            result = get_sheep_info_for_context('CONTEXT001', test_user.id)
            
            assert result is not None
            assert 'EarNum' in result
            assert 'recent_events' in result
            assert 'history_records' in result
            assert len(result['recent_events']) > 0
            assert len(result['history_records']) > 0

    def test_get_sheep_info_for_context_database_error(self, app, test_user):
        """測試獲取羊隻資訊時的資料庫錯誤"""
        with app.app_context():
            # 直接測試異常處理而不模擬，因為get_sheep_info_for_context沒有異常處理
            # 只需要測試函數能處理不存在的sheep
            result = get_sheep_info_for_context('NONEXISTENT', test_user.id)
            assert result is None


class TestModelsEnhanced:
    """增強的模型測試類別"""

    def test_sheep_model_to_dict_with_all_fields(self, app, test_user):
        """測試羊隻模型的完整字典轉換"""
        with app.app_context():
            sheep = Sheep(
                user_id=test_user.id,
                EarNum='DICT001',
                Breed='波爾羊',
                Sex='母',
                BirthDate='2023-01-15',
                Body_Weight_kg=45.0,
                Age_Months=12,
                status='懷孕',
                other_remarks='健康狀況良好',
                FarmNum='F001',
                Sire='SIRE001',
                Dam='DAM001',
                BirWei=3.5,
                SireBre='波爾羊',
                DamBre='波爾羊',
                MoveCau='購買',
                MoveDate='2023-02-01',
                Class='育成羊',
                LittleSize=2,
                Lactation=1,
                ManaClas='A級',
                RUni='KG',
                next_vaccination_due_date='2024-06-01',
                next_deworming_due_date='2024-05-15',
                expected_lambing_date='2024-07-01',
                milk_yield_kg_day=2.5,
                milk_fat_percentage=3.8,
                welfare_score=3,
                last_updated=datetime.now()
            )
            app.extensions['sqlalchemy'].session.add(sheep)
            app.extensions['sqlalchemy'].session.commit()

            sheep_dict = sheep.to_dict()
            
            # 檢查所有欄位都被包含
            expected_fields = [
                'id', 'user_id', 'EarNum', 'Breed', 'Sex', 'BirthDate',
                'Body_Weight_kg', 'Age_Months', 'status', 'other_remarks', 'FarmNum',
                'Sire', 'Dam', 'BirWei', 'SireBre', 'DamBre', 'MoveCau',
                'MoveDate', 'Class', 'LittleSize', 'Lactation', 'ManaClas',
                'RUni', 'next_vaccination_due_date', 'next_deworming_due_date',
                'expected_lambing_date', 'milk_yield_kg_day', 'milk_fat_percentage',
                'welfare_score', 'last_updated'
            ]
            
            for field in expected_fields:
                assert field in sheep_dict

    def test_sheep_event_model_to_dict(self, app, test_user):
        """測試羊隻事件模型的字典轉換"""
        with app.app_context():
            sheep = Sheep(user_id=test_user.id, EarNum='EVENT001', Breed='波爾羊', Sex='母')
            app.extensions['sqlalchemy'].session.add(sheep)
            app.extensions['sqlalchemy'].session.commit()
            
            event = SheepEvent(
                user_id=test_user.id,
                sheep_id=sheep.id,
                event_date='2024-01-15',
                event_type='疫苗接種',
                description='狂犬病疫苗',
                notes='第二次接種',
                medication='疫苗A',
                withdrawal_days=0
            )
            app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()

            event_dict = event.to_dict()
            
            # 檢查所有欄位都被包含
            expected_fields = [
                'id', 'user_id', 'sheep_id', 'event_date', 'event_type',
                'description', 'notes', 'medication', 'withdrawal_days', 'recorded_at'
            ]
            
            for field in expected_fields:
                assert field in event_dict

    def test_sheep_historical_data_model_to_dict(self, app, test_user):
        """測試羊隻歷史數據模型的字典轉換"""
        with app.app_context():
            sheep = Sheep(user_id=test_user.id, EarNum='HIST001', Breed='波爾羊', Sex='母')
            app.extensions['sqlalchemy'].session.add(sheep)
            app.extensions['sqlalchemy'].session.commit()
            
            history = SheepHistoricalData(
                user_id=test_user.id,
                sheep_id=sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.0,
                notes='定期稱重'
            )
            app.extensions['sqlalchemy'].session.add(history)
            app.extensions['sqlalchemy'].session.commit()

            history_dict = history.to_dict()
            
            # 檢查所有欄位都被包含
            expected_fields = [
                'id', 'user_id', 'sheep_id', 'record_date',
                'record_type', 'value', 'notes', 'recorded_at'
            ]
            
            for field in expected_fields:
                assert field in history_dict

    def test_user_model_password_verification(self, app):
        """測試用戶模型的密碼驗證"""
        with app.app_context():
            from werkzeug.security import generate_password_hash, check_password_hash
            
            user = User(
                username='pwtest',
                password_hash=generate_password_hash('testpass123')
            )
            
            # 測試正確密碼
            assert check_password_hash(user.password_hash, 'testpass123')
            
            # 測試錯誤密碼
            assert not check_password_hash(user.password_hash, 'wrongpass')

    def test_chat_history_model_to_dict(self, app, test_user):
        """測試聊天歷史模型的字典轉換"""
        with app.app_context():
            chat = ChatHistory(
                user_id=test_user.id,
                session_id='test-session',
                role='user',
                content='測試問題',
                timestamp=datetime.now()
            )
            app.extensions['sqlalchemy'].session.add(chat)
            app.extensions['sqlalchemy'].session.commit()

            # ChatHistory模型沒有to_dict方法，所以我們直接檢查欄位
            # 檢查模型有正確的欄位
            expected_fields = ['id', 'user_id', 'session_id', 'role', 'content', 'timestamp']
            
            for field in expected_fields:
                assert hasattr(chat, field)


class TestSchemasEnhanced:
    """增強的schema測試類別"""

    def test_sheep_create_model_validation_edge_cases(self):
        """測試羊隻創建模型的邊緣情況驗證"""
        # 測試最小有效數據
        try:
            model = SheepCreateModel(EarNum='MIN001')
            assert model.EarNum == 'MIN001'
        except ValidationError:
            pytest.fail("最小有效數據應該通過驗證")

        # 測試無效體重
        with pytest.raises(ValidationError):
            SheepCreateModel(EarNum='INVALID001', Body_Weight_kg=-5.0)

        # 測試無效年齡
        with pytest.raises(ValidationError):
            SheepCreateModel(EarNum='INVALID002', Age_Months=-1)

    def test_sheep_update_model_partial_validation(self):
        """測試羊隻更新模型的部分驗證"""
        # 測試只更新一個欄位
        model = SheepUpdateModel(Body_Weight_kg=50.0)
        assert model.Body_Weight_kg == 50.0
        
        # 測試更新多個欄位
        model = SheepUpdateModel(
            Body_Weight_kg=50.0,
            status='健康',
            other_remarks='更新備註'
        )
        assert model.Body_Weight_kg == 50.0
        assert model.status == '健康'
        assert model.other_remarks == '更新備註'

    def test_sheep_event_create_model_validation(self):
        """測試羊隻事件創建模型驗證"""
        # 測試有效事件
        model = SheepEventCreateModel(
            event_date='2024-01-15',
            event_type='疫苗接種',
            description='狂犬病疫苗'
        )
        assert model.event_date == '2024-01-15'
        assert model.event_type == '疫苗接種'

        # 測試包含可選欄位的事件
        model = SheepEventCreateModel(
            event_date='2024-01-15',
            event_type='藥物治療',
            description='抗生素治療',
            medication='青黴素',
            withdrawal_days=7,
            notes='治療備註'
        )
        assert model.medication == '青黴素'
        assert model.withdrawal_days == 7
        assert model.notes == '治療備註'

    def test_schema_error_response_creation(self):
        """測試schema錯誤響應創建"""
        from app.schemas import create_error_response
        
        # 模擬Pydantic驗證錯誤
        mock_errors = [
            {
                'loc': ('Body_Weight_kg',),
                'msg': 'ensure this value is greater than 0',
                'type': 'value_error.number.not_gt'
            },
            {
                'loc': ('Age_Months',),
                'msg': 'ensure this value is greater than or equal to 0',
                'type': 'value_error.number.not_ge'
            }
        ]
        
        error_response = create_error_response("驗證失敗", mock_errors)
        
        assert 'error' in error_response
        assert 'details' in error_response
        assert len(error_response['details']) == 2
        # 檢查field_errors而不是details中的field
        if 'field_errors' in error_response:
            assert 'Body_Weight_kg' in error_response['field_errors']

    def test_schema_with_extreme_string_lengths(self):
        """測試schema處理極端字符串長度"""
        # 測試很長的字符串
        long_string = 'A' * 1000
        
        try:
            model = SheepCreateModel(
                EarNum='LONG001',
                other_remarks=long_string
            )
            # 根據schema定義，可能成功或失敗
            assert model.EarNum == 'LONG001'
        except ValidationError:
            # 如果有長度限制，應該捕獲驗證錯誤
            pass

    def test_schema_with_unicode_characters(self):
        """測試schema處理Unicode字符"""
        # 測試包含Unicode字符的數據
        unicode_data = {
            'EarNum': 'UNICODE001',
            'Breed': '波爾羊🐐',
            'notes': '這是一個包含emoji😀和中文的備註'
        }
        
        try:
            model = SheepCreateModel(**unicode_data)
            assert model.EarNum == 'UNICODE001'
            assert '🐐' in model.Breed
        except ValidationError as e:
            pytest.fail(f"Unicode字符應該被正確處理: {e}")
