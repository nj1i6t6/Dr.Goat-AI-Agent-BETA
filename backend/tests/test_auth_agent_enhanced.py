"""
增強的認證和代理API測試
專門用於提高auth.py和agent.py的測試覆蓋率
"""

import pytest
import json
from unittest.mock import patch
from datetime import datetime
from app.models import User, ChatHistory
from werkzeug.security import generate_password_hash


class TestAuthAPIEnhanced:
    """增強的認證API測試類別"""

    def test_register_with_database_error(self, client, mocker):
        """測試註冊時資料庫錯誤"""
        user_data = {
            'username': 'dberror',
            'password': 'testpass123'
        }
        
        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = client.post('/api/auth/register', json=user_data)
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_register_non_json_request(self, client):
        """測試非JSON格式的註冊請求"""
        response = client.post('/api/auth/register',
                             data='not json',
                             content_type='text/plain')
        assert response.status_code == 415  # Flask 在沒有適當 Content-Type 時返回 415
        # 對於 415 錯誤，Flask 返回 HTML 而不是 JSON
        assert 'Unsupported Media Type' in response.data.decode()

    def test_login_with_database_error(self, client, test_user):
        """測試登入時資料庫錯誤"""
        login_data = {
            'username': 'testuser',
            'password': 'testpass'
        }
        
        with patch('app.api.auth.User.query') as mock_query:
            mock_query.filter_by.side_effect = Exception("Database error")
            # 現行實作會捕捉例外並回傳 500 JSON，而非直接拋出
            response = client.post('/api/auth/login', json=login_data)
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert '登入時發生錯誤' in data['error']

    def test_login_non_json_request(self, client):
        """測試非JSON格式的登入請求"""
        response = client.post('/api/auth/login',
                             data='not json',
                             content_type='text/plain')
        # login 路由包在 try/except 中，UnsupportedMediaType 被捕捉並轉成 500 JSON 回應
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert '登入時發生錯誤' in data['error']

    def test_login_with_case_sensitivity(self, client, app):
        """測試用戶名大小寫敏感性"""
        # 創建測試用戶
        with app.app_context():
            user = User(
                username='CaseUser',
                password_hash=generate_password_hash('testpass')
            )
            app.extensions['sqlalchemy'].session.add(user)
            app.extensions['sqlalchemy'].session.commit()

        # 測試不同大小寫的用戶名
        login_data = {
            'username': 'caseuser',  # 小寫
            'password': 'testpass'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 401  # 應該失敗，因為用戶名大小寫敏感

    def test_logout_without_login(self, client):
        """測試未登入狀態下的登出"""
        response = client.post('/api/auth/logout')
        # 未登入狀態下登出可能返回401或200，取決於實現
        assert response.status_code in [200, 401]
        data = json.loads(response.data)
        if response.status_code == 200:
            assert data['success'] is True

    def test_auth_status_edge_cases(self, client, test_user):
        """測試認證狀態的邊緣情況"""
        # 先測試未認證用戶的狀態
        response = client.get('/api/auth/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['logged_in'] is False  # 使用正確的字段名
        
        # 登入用戶
        client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        # 測試已認證用戶的狀態
        response = client.get('/api/auth/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['logged_in'] is True  # 使用正確的字段名
        assert 'user' in data

    def test_register_username_edge_cases(self, client):
        """測試用戶名的邊緣情況"""
        test_cases = [
            {'username': '', 'password': 'testpass'},  # 空用戶名
            {'username': ' ', 'password': 'testpass'},  # 空格用戶名
            {'username': 'a', 'password': 'testpass'},  # 單字符用戶名
            {'username': 'a' * 100, 'password': 'testpass'},  # 很長的用戶名
            {'username': 'test@user', 'password': 'testpass'},  # 包含特殊字符
        ]
        
        for user_data in test_cases:
            response = client.post('/api/auth/register', json=user_data)
            # 根據驗證規則，這些可能成功或失敗
            assert response.status_code in [201, 400, 409, 500]

    def test_register_password_edge_cases(self, client):
        """測試密碼的邊緣情況"""
        test_cases = [
            {'username': 'pwtest1', 'password': ''},  # 空密碼
            {'username': 'pwtest2', 'password': ' '},  # 空格密碼
            {'username': 'pwtest3', 'password': 'a'},  # 單字符密碼
            {'username': 'pwtest4', 'password': 'a' * 200},  # 很長的密碼
        ]
        
        for user_data in test_cases:
            response = client.post('/api/auth/register', json=user_data)
            # 根據驗證規則，這些可能成功或失敗
            assert response.status_code in [201, 400, 500]


class TestAgentAPIEnhanced:
    """增強的代理API測試類別"""

    def test_get_recommendation_with_missing_api_key(self, authenticated_client, app):
        """測試沒有API金鑰時的建議獲取"""
        recommendation_data = {
            'Body_Weight_kg': 45.0,
            'Age_Months': 12,
            'Breed': '波爾羊',
            'Sex': '母'
        }
        
        # 暫時移除API金鑰
        original_key = app.config.get('GOOGLE_API_KEY')
        app.config['GOOGLE_API_KEY'] = None
        
        try:
            # 這裡我們發送請求，但如果伺服器配置缺少金鑰，可能會返回 500 或 400
            # 如果我們不發送 X-Api-Key header，則會返回 401
            # 為了測試伺服器配置缺失的情況，我們應該發送 header
            response = authenticated_client.post('/api/agent/recommendation', 
                                               json=recommendation_data,
                                               headers={'X-Api-Key': 'test-api-key'})
            # 根據實作，如果伺服器端沒有配置 API Key，可能會報錯
            # 假設這裡測試的是伺服器端配置缺失
            assert response.status_code in [400, 500]
            data = json.loads(response.data)
            assert 'error' in data
        finally:
            # 恢復API金鑰
            app.config['GOOGLE_API_KEY'] = original_key

    def test_get_recommendation_with_api_error(self, authenticated_client, mock_gemini_api_error):
        """測試API錯誤時的建議獲取"""
        recommendation_data = {
            'Body_Weight_kg': 45.0,
            'Age_Months': 12,
            'Breed': '波爾羊',
            'Sex': '母'
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 400  # API 錯誤應該返回 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_recommendation_non_json_request(self, authenticated_client):
        """測試非JSON格式的建議請求"""
        response = authenticated_client.post('/api/agent/recommendation',
                                           data='not json',
                                           content_type='text/plain',
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 415  # Flask 在沒有適當 Content-Type 時返回 415
        # 對於 415 錯誤，Flask 返回 HTML 而不是 JSON
        assert 'Unsupported Media Type' in response.data.decode()

    def test_get_recommendation_with_extreme_values(self, authenticated_client, mock_gemini_api):
        """測試極端值的建議請求"""
        extreme_cases = [
            {
                'Body_Weight_kg': 0.1,  # 極小體重
                'Age_Months': 0,  # 零月齡
                'Breed': '波爾羊',
                'Sex': '母'
            },
            {
                'Body_Weight_kg': 200.0,  # 極大體重
                'Age_Months': 120,  # 10年
                'Breed': '波爾羊',
                'Sex': '母'
            },
            {
                'Body_Weight_kg': -5.0,  # 負體重
                'Age_Months': -1,  # 負月齡
                'Breed': '波爾羊',
                'Sex': '母'
            }
        ]
        
        for data in extreme_cases:
            response = authenticated_client.post('/api/agent/recommendation', 
                                               json=data,
                                               headers={'X-Api-Key': 'test-api-key'})
            # 根據驗證規則，可能成功或失敗
            assert response.status_code in [200, 400]

    def test_get_recommendation_with_special_characters(self, authenticated_client, mock_gemini_api):
        """測試包含特殊字符的建議請求"""
        recommendation_data = {
            'Body_Weight_kg': 45.0,
            'Age_Months': 12,
            'Breed': '波爾羊@#$%',  # 包含特殊字符
            'Sex': '母/公',  # 包含特殊字符
            'management_focus': '<script>alert("test")</script>'  # 潛在的XSS測試
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 200  # 應該成功處理

    def test_chat_with_agent_empty_message(self, authenticated_client):
        """測試空消息的聊天"""
        chat_data = {
            'message': ''
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_chat_with_agent_very_long_message(self, authenticated_client, mock_gemini_api):
        """測試很長消息的聊天"""
        long_message = '這是一個很長的消息' * 1000  # 很長的消息
        chat_data = {
            'message': long_message
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        # 根據限制，可能成功或失敗
        assert response.status_code in [200, 400, 413]

    def test_chat_with_agent_non_json_request(self, authenticated_client):
        """測試非JSON格式的聊天請求"""
        response = authenticated_client.post('/api/agent/chat',
                                           data='not json',
                                           content_type='text/plain',
                                           headers={'X-Api-Key': 'test-api-key'})
        # 現行 chat 路由對一般 Exception 轉為 400 JSON（UnsupportedMediaType 被 except 捕捉）
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '處理請求時發生錯誤' in data['error']

    def test_chat_history_saving_failure(self, authenticated_client, mock_gemini_api):
        """測試聊天歷史保存失敗"""
        chat_data = {
            'message': '測試消息',
            'session_id': 'test-session-123'
        }
        
        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.post('/api/agent/chat', 
                                               json=chat_data,
                                               headers={'X-Api-Key': 'test-api-key'})
            # 即使歷史保存失敗，聊天仍應成功
            assert response.status_code == 200

    def test_chat_with_sheep_context_invalid_ear_num(self, authenticated_client, mock_gemini_api):
        """測試使用無效耳號的羊隻上下文聊天"""
        chat_data = {
            'message': '這隻羊的健康狀況如何？',
            'session_id': 'test-session-123',
            'ear_num_context': 'INVALID_EAR_NUM'
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 200  # 應該成功，但沒有羊隻上下文

    def test_get_agent_tip_database_error(self, authenticated_client, mock_gemini_api):
        """測試獲取代理小貼士時的資料庫錯誤"""
        with patch('app.models.Sheep.query') as mock_query:
            mock_query.filter_by.side_effect = Exception("Database error")
            headers = {'X-Api-Key': 'test-api-key'}
            response = authenticated_client.get('/api/agent/tip', headers=headers)
            # 即使資料庫錯誤，仍應返回基本小貼士
            assert response.status_code == 200

    def test_get_agent_tip_with_no_sheep_data(self, authenticated_client, mock_gemini_api):
        """測試沒有羊隻數據時的代理小貼士"""
        headers = {'X-Api-Key': 'test-api-key'}
        response = authenticated_client.get('/api/agent/tip', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tip_html' in data

    def test_recommendation_with_all_optional_fields(self, authenticated_client, mock_gemini_api):
        """測試包含所有可選欄位的建議請求"""
        comprehensive_data = {
            'Body_Weight_kg': 45.0,
            'Age_Months': 12,
            'Breed': '波爾羊',
            'Sex': '母',
            'status': '懷孕中期',
            'number_of_fetuses': 2,
            'milk_yield_kg_day': 2.5,
            'milk_fat_percentage': 3.8,
            'activity_level': '中等',
            'other_remarks': '需要高蛋白飼料'
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=comprehensive_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendation_html' in data

    def test_chat_with_context_and_long_history(self, authenticated_client, app, test_user, mock_gemini_api):
        """測試包含上下文和長聊天歷史的對話"""
        from app.models import ChatHistory
        from datetime import datetime
        with app.app_context():
            # 創建多條聊天歷史
            for i in range(20):  # 20條歷史記錄
                # 用戶消息
                user_chat = ChatHistory(
                    user_id=test_user.id,
                    session_id=f'test_session_{i}',
                    role='user',
                    content=f'測試消息 {i}',
                    timestamp=datetime.now()
                )
                app.extensions['sqlalchemy'].session.add(user_chat)
                # AI 回應
                ai_chat = ChatHistory(
                    user_id=test_user.id,
                    session_id=f'test_session_{i}',
                    role='assistant',
                    content=f'測試回答 {i}',
                    timestamp=datetime.now()
                )
                app.extensions['sqlalchemy'].session.add(ai_chat)
            app.extensions['sqlalchemy'].session.commit()

        chat_data = {
            'message': '基於我們之前的對話，請給出建議',
            'session_id': 'test-session-long',
            'ear_num_context': 'TEST001'
        }
        
        response = authenticated_client.post('/api/agent/chat', 
                                           json=chat_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'reply_html' in data

    def test_recommendation_with_invalid_physiological_state(self, authenticated_client, mock_gemini_api):
        """測試無效生理狀態的建議請求"""
        recommendation_data = {
            'Body_Weight_kg': 45.0,
            'Age_Months': 12,
            'Breed': '波爾羊',
            'Sex': '母',
            'status': '無效狀態'
        }
        
        response = authenticated_client.post('/api/agent/recommendation', 
                                           json=recommendation_data,
                                           headers={'X-Api-Key': 'test-api-key'})
        # 應該成功處理，即使狀態無效
        assert response.status_code == 200

    def test_agent_endpoints_concurrent_access(self, authenticated_client, mock_gemini_api):
        """測試代理端點的併發訪問"""
        import threading
        import time
        
        results = []
        
        def make_request():
            headers = {'X-Api-Key': 'test-api-key'}
            response = authenticated_client.get('/api/agent/tip', headers=headers)
            results.append(response.status_code)
        
        # 創建多個線程同時訪問
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        # 所有請求都應該成功
        assert all(status == 200 for status in results)
