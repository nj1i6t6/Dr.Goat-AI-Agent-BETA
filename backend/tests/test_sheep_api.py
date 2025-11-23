"""
山羊管理 API 測試
測試山羊 CRUD 功能
"""

import pytest
import json
from app.models import Sheep


class TestSheepAPI:
    """山羊 API 測試類別"""

    def test_get_sheep_list_authenticated(self, authenticated_client):
        """測試已認證用戶獲取山羊列表"""
        response = authenticated_client.get('/api/sheep/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_get_sheep_list_unauthenticated(self, client):
        """測試未認證用戶獲取山羊列表"""
        response = client.get('/api/sheep/')
        
        assert response.status_code == 401

    def test_create_sheep_success(self, authenticated_client):
        """測試成功創建山羊"""
        sheep_data = {
            'EarNum': 'CREATE001',
            'Breed': '波爾羊',
            'Sex': '母',
            'Body_Weight_kg': 45.5
        }
        
        response = authenticated_client.post('/api/sheep/', json=sheep_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'sheep' in data
        assert data['sheep']['EarNum'] == 'CREATE001'

    def test_create_sheep_validation_error(self, authenticated_client):
        """測試創建山羊資料驗證錯誤"""
        # 缺少必要欄位
        response = authenticated_client.post('/api/sheep/', json={})
        assert response.status_code == 400
        
        # 無效體重
        sheep_data = {
            'EarNum': 'INVALID001',
            'Body_Weight_kg': -10.0  # 負數體重
        }
        response = authenticated_client.post('/api/sheep/', json=sheep_data)
        assert response.status_code == 400

    def test_create_duplicate_sheep(self, authenticated_client, test_sheep):
        """測試創建重複耳號的山羊"""
        sheep_data = {
            'EarNum': 'TEST001',  # 已存在的耳號
            'Breed': '波爾羊',
            'Sex': '母'
        }
        
        response = authenticated_client.post('/api/sheep/', json=sheep_data)
        
        assert response.status_code == 409  # 實際 API 返回 409
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_sheep_by_earnum_success(self, authenticated_client, test_sheep):
        """測試成功獲取特定山羊"""
        response = authenticated_client.get('/api/sheep/TEST001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['EarNum'] == 'TEST001'

    def test_get_sheep_by_earnum_not_found(self, authenticated_client):
        """測試獲取不存在的山羊"""
        response = authenticated_client.get('/api/sheep/NOTFOUND')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_update_sheep_success(self, authenticated_client, test_sheep):
        """測試成功更新山羊資料"""
        update_data = {
            'Body_Weight_kg': 55.0,
            'status': '健康'
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_update_sheep_not_found(self, authenticated_client):
        """測試更新不存在的山羊"""
        update_data = {'Body_Weight_kg': 55.0}
        
        response = authenticated_client.put('/api/sheep/NOTFOUND', json=update_data)
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_update_sheep_validation_error(self, authenticated_client, test_sheep):
        """測試更新山羊資料驗證錯誤"""
        update_data = {
            'Body_Weight_kg': -20.0  # 無效體重
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'field_errors' in data

    def test_delete_sheep_success(self, authenticated_client, test_sheep):
        """測試成功刪除山羊"""
        response = authenticated_client.delete('/api/sheep/TEST001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_delete_sheep_not_found(self, authenticated_client):
        """測試刪除不存在的山羊"""
        response = authenticated_client.delete('/api/sheep/NOTFOUND')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_sheep_unauthenticated_access(self, client):
        """測試未認證用戶訪問山羊 API"""
        # 創建
        response = client.post('/api/sheep/', json={'EarNum': 'TEST'})
        assert response.status_code == 401
        
        # 獲取
        response = client.get('/api/sheep/TEST001')
        assert response.status_code == 401
        
        # 更新
        response = client.put('/api/sheep/TEST001', json={'Body_Weight_kg': 50})
        assert response.status_code == 401
        
        # 刪除
        response = client.delete('/api/sheep/TEST001')
        assert response.status_code == 401
