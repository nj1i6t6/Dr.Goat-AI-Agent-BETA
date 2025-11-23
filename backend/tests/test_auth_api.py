"""
認證 API 測試
測試登錄、註冊、登出等功能
"""

import pytest
import json
from app.models import User


class TestAuthAPI:
    """認證 API 測試類別"""

    def test_register_success(self, client):
        """測試成功註冊"""
        register_data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        
        response = client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'message' in data

    def test_register_duplicate_user(self, client, test_user):
        """測試重複用戶註冊"""
        register_data = {
            'username': 'testuser',  # 已存在的用戶
            'password': 'newpass123'
        }
        
        response = client.post('/api/auth/register', json=register_data)
        
        assert response.status_code == 409  # 實際 API 返回 409
        data = json.loads(response.data)
        assert 'error' in data

    def test_login_success(self, client, test_user):
        """測試成功登錄"""
        login_data = {
            'username': 'testuser',
            'password': 'testpass'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['username'] == 'testuser'

    def test_login_invalid_credentials(self, client, test_user):
        """測試無效憑證登錄"""
        login_data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_login_nonexistent_user(self, client):
        """測試不存在用戶登錄"""
        login_data = {
            'username': 'nonexistent',
            'password': 'somepass'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_auth_status_authenticated(self, authenticated_client):
        """測試已認證用戶的狀態檢查"""
        response = authenticated_client.get('/api/auth/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['logged_in'] is True  # 實際 API 返回 logged_in
        assert 'user' in data

    def test_auth_status_unauthenticated(self, client):
        """測試未認證用戶的狀態檢查"""
        response = client.get('/api/auth/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['logged_in'] is False  # 實際 API 返回 logged_in

    def test_logout_success(self, authenticated_client):
        """測試成功登出"""
        response = authenticated_client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_login_validation_errors(self, client):
        """測試登錄資料驗證錯誤"""
        # 缺少密碼 - API 會直接返回 401（無效認證）
        response = client.post('/api/auth/login', json={'username': 'test'})
        assert response.status_code == 401
        
        # 缺少用戶名 - API 會直接返回 401（無效認證）
        response = client.post('/api/auth/login', json={'password': 'test'})
        assert response.status_code == 401
        
        # 空用戶名 - API 會直接返回 401（無效認證）
        response = client.post('/api/auth/login', json={'username': '', 'password': 'test'})
        assert response.status_code == 401

    def test_register_validation_errors(self, client):
        """測試註冊資料驗證錯誤"""
        # 缺少密碼
        response = client.post('/api/auth/register', json={'username': 'test'})
        assert response.status_code == 400
        
        # 缺少用戶名
        response = client.post('/api/auth/register', json={'password': 'test'})
        assert response.status_code == 400
        
        # 空用戶名
        response = client.post('/api/auth/register', json={'username': '', 'password': 'test'})
        assert response.status_code == 400
