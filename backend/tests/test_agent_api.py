"""
agent.py API 測試
測試 AI 代理人相關的 API 端點
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app.models import ChatHistory


class TestAgentAPI:
    """Agent API 測試類別"""

    def test_get_agent_tip_success(self, authenticated_client, mock_gemini_api):
        """測試成功獲取每日提示"""
        response = authenticated_client.get('/api/agent/tip', headers={
            'X-Api-Key': 'test-api-key'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tip_html' in data
        assert len(data['tip_html']) > 0

    def test_get_agent_tip_sanitizes_html(self, authenticated_client, monkeypatch):
        """確保每日提示的 HTML 內容被妥善清理"""

        def malicious_call_gemini_api(*args, **kwargs):
            return {
                "text": "危險<script>alert('x')</script> [連結](javascript:alert('bad')) <a href='https://example.com'>安全連結</a>"
            }

        monkeypatch.setattr('app.api.agent.call_gemini_api', malicious_call_gemini_api)

        response = authenticated_client.get('/api/agent/tip', headers={'X-Api-Key': 'test-api-key'})

        assert response.status_code == 200
        data = json.loads(response.data)
        tip_html = data.get('tip_html', '')
        assert '<script>' not in tip_html
        assert 'javascript:' not in tip_html
        assert 'noopener' in tip_html
        assert 'noreferrer' in tip_html
        assert 'nofollow' in tip_html
        assert 'rel="noopener noreferrer nofollow">連結</a>' in tip_html
        assert 'target="_blank"' in tip_html

    def test_get_agent_tip_missing_api_key(self, authenticated_client):
        """測試缺少 API 金鑰的情況"""
        response = authenticated_client.get('/api/agent/tip')

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'API金鑰' in data['error']

    def test_get_agent_tip_api_error(self, authenticated_client, mock_gemini_api_error):
        """測試 Gemini API 錯誤的情況"""
        response = authenticated_client.get('/api/agent/tip', headers={
            'X-Api-Key': 'test-api-key'
        })
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_recommendation_success(self, authenticated_client, mock_gemini_api):
        """測試成功獲取飼養建議"""
        recommendation_data = {
            'EarNum': 'TEST001',
            'Breed': '波爾羊',
            'Body_Weight_kg': 45.5,
            'Age_Months': 12,
            'Sex': '母',
            'status': '懷孕'
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendation_html' in data
        assert len(data['recommendation_html']) > 0

    def test_get_recommendation_validation_error(self, authenticated_client):
        """測試資料驗證錯誤"""
        # 缺少必要的欄位 (例如 Body_Weight_kg)
        recommendation_data = {
            'EarNum': 'TEST001',
            'Breed': '波爾羊'
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'field_errors' in data

    def test_get_recommendation_with_invalid_weight(self, authenticated_client):
        """測試體重驗證"""
        recommendation_data = {
            'EarNum': 'TEST001',
            'Body_Weight_kg': -10.0  # 負數體重應該失敗
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'field_errors' in data
        assert 'Body_Weight_kg' in data['field_errors']

    def test_get_recommendation_with_sheep_context(self, authenticated_client, 
                                                 test_sheep, mock_gemini_api):
        """測試包含羊隻背景資料的建議"""
        # 使用已知的 EarNum 而不是訪問對象屬性
        recommendation_data = {
            'EarNum': 'TEST001',  # 使用固定的耳號
            'Body_Weight_kg': 50.0
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendation_html' in data

    def test_chat_with_agent_success(self, authenticated_client, mock_gemini_api):
        """測試成功的聊天互動"""
        chat_data = {
            'message': '請問羊隻的最佳飼養溫度是多少？',
            'session_id': 'test-session-001'
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'reply_html' in data

    def test_agent_status_requires_api_key(self, authenticated_client):
        response = authenticated_client.get('/api/agent/status')
        assert response.status_code == 401

    def test_agent_status_reports_rag_state(self, authenticated_client, monkeypatch):
        monkeypatch.setattr(
            'app.api.agent.get_rag_status',
            lambda: {'available': True, 'message': 'RAG OK', 'detail': 'vectors.parquet'},
        )

        response = authenticated_client.get(
            '/api/agent/status', headers={'X-Api-Key': 'valid-key'}
        )

        assert response.status_code == 200
        payload = json.loads(response.data)
        assert payload['rag_enabled'] is True
        assert payload['message'] == 'RAG OK'
        assert payload['detail'] == 'vectors.parquet'

    def test_chat_with_agent_validation_error(self, authenticated_client):
        """測試聊天資料驗證錯誤"""
        # 缺少必要欄位
        chat_data = {
            'message': '測試訊息'
            # 缺少 session_id
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'field_errors' in data

    def test_chat_with_sheep_context(self, authenticated_client, test_sheep, mock_gemini_api):
        """測試包含羊隻上下文的聊天"""
        chat_data = {
            'message': '這隻羊隻的健康狀況如何？',
            'session_id': 'test-session-002',
            'ear_num_context': 'TEST001'  # 使用固定的耳號
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'reply_html' in data

    def test_chat_history_saved(self, authenticated_client, test_user, mock_gemini_api):
        """測試聊天記錄是否正確儲存"""
        chat_data = {
            'message': '測試訊息',
            'session_id': 'test-session-003'
        }
        
        # 執行聊天
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 200
        
        # 重新獲取用戶ID以避免會話問題
        from app.models import User
        user = User.query.filter_by(username='testuser').first()
        user_id = user.id
        
        # 檢查資料庫中的聊天記錄
        user_message = ChatHistory.query.filter_by(
            user_id=user_id,
            session_id='test-session-003',
            role='user'
        ).first()
        
        model_message = ChatHistory.query.filter_by(
            user_id=user_id,
            session_id='test-session-003',
            role='model'
        ).first()
        
        assert user_message is not None
        assert user_message.content == '測試訊息'
        assert model_message is not None
        assert len(model_message.content) > 0

    def test_chat_api_error_handling(self, authenticated_client, mock_gemini_api_error):
        """測試 API 錯誤處理"""
        chat_data = {
            'message': '測試訊息',
            'session_id': 'test-session-004'
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_recommendation_with_all_fields(self, authenticated_client, mock_gemini_api):
        """測試包含所有欄位的飼養建議請求"""
        recommendation_data = {
            'EarNum': 'FULL001',
            'Breed': '波爾羊',
            'Body_Weight_kg': 45.5,
            'Age_Months': 18,
            'Sex': '母',
            'status': '哺乳',
            'target_average_daily_gain_g': 150.0,
            'milk_yield_kg_day': 2.5,
            'milk_fat_percentage': 4.2,
            'number_of_fetuses': 2,
            'other_remarks': '這隻羊隻食慾良好，活動力正常。'
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendation_html' in data

    def test_unauthenticated_access(self, client):
        """測試未認證用戶的訪問"""
        # 測試每日提示
        response = client.get('/api/agent/tip', headers={
            'X-Api-Key': 'test-api-key'
        })
        assert response.status_code == 401

        # 測試飼養建議
        response = client.post('/api/agent/recommendation', json={
            'EarNum': 'TEST001'
        })
        assert response.status_code == 401

        # 測試聊天
        response = client.post('/api/agent/chat', json={
            'message': '測試',
            'session_id': 'test'
        })
        assert response.status_code == 401

    @pytest.mark.parametrize("field,invalid_value,expected_error", [
        ('Body_Weight_kg', -5.0, '體重'),
        ('Age_Months', -1, '月齡'),
        ('milk_fat_percentage', 150.0, '乳脂率'),
        ('number_of_fetuses', -1, '懷胎數'),
    ])
    def test_recommendation_field_validation(self, authenticated_client, 
                                           field, invalid_value, expected_error):
        """測試各欄位的驗證邏輯"""
        recommendation_data = {
            'EarNum': 'VALID001',
            field: invalid_value
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'field_errors' in data
        assert field in data['field_errors']
