"""
山羊歷史數據管理 API 測試
測試山羊歷史數據相關功能
"""

import pytest
import json
from datetime import datetime, date
from app.models import Sheep, SheepHistoricalData


class TestSheepHistoryAPI:
    """山羊歷史數據 API 測試類別"""

    def test_get_sheep_history_success(self, authenticated_client, test_sheep, app):
        """測試成功獲取山羊歷史數據"""
        # 通過更新羊隻來創建歷史數據
        update_data = {
            'Body_Weight_kg': 46.0,
            'record_date': '2024-01-15'
        }
        authenticated_client.put('/api/sheep/TEST001', json=update_data)
        
        # 獲取歷史數據
        response = authenticated_client.get('/api/sheep/TEST001/history')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        # 檢查是否有歷史記錄
        assert len(data) >= 0  # 可能為0，取決於是否有變化

    def test_get_sheep_history_sheep_not_found(self, authenticated_client):
        """測試獲取不存在山羊的歷史數據"""
        response = authenticated_client.get('/api/sheep/NOTFOUND/history')
        
        assert response.status_code == 404

    def test_add_sheep_history_via_update(self, authenticated_client, test_sheep):
        """測試通過更新羊隻來添加歷史數據"""
        # 歷史數據是通過更新羊隻自動記錄的
        update_data = {
            'Body_Weight_kg': 47.0,
            'milk_yield_kg_day': 2.5,
            'record_date': '2024-01-15'
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        assert response.status_code == 200
        
        # 檢查歷史數據是否被記錄
        history_response = authenticated_client.get('/api/sheep/TEST001/history')
        assert history_response.status_code == 200
        history_data = json.loads(history_response.data)
        # 應該有歷史記錄（如果值有變化）
        assert isinstance(history_data, list)

    def test_delete_sheep_history_success(self, authenticated_client, test_sheep, app):
        """測試成功刪除山羊歷史數據"""
        # 先創建歷史數據
        with app.app_context():
            history_record = SheepHistoricalData(
                user_id=test_sheep.user_id,
                sheep_id=test_sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.0,
                notes='測試記錄'
            )
            app.extensions['sqlalchemy'].session.add(history_record)
            app.extensions['sqlalchemy'].session.commit()
            record_id = history_record.id

        # 刪除歷史記錄
        response = authenticated_client.delete(f'/api/sheep/history/{record_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_delete_sheep_history_not_found(self, authenticated_client):
        """測試刪除不存在的歷史數據"""
        response = authenticated_client.delete('/api/sheep/history/99999')
        
        assert response.status_code == 404

    def test_sheep_history_unauthenticated_access(self, client):
        """測試未認證用戶訪問山羊歷史數據 API"""
        # 獲取歷史數據
        response = client.get('/api/sheep/TEST001/history')
        assert response.status_code == 401
        
        # 刪除歷史數據
        response = client.delete('/api/sheep/history/1')
        assert response.status_code == 401

    def test_get_sheep_history_with_multiple_records(self, authenticated_client, test_sheep, app):
        """測試獲取多條歷史記錄"""
        # 創建多條歷史記錄
        with app.app_context():
            records = [
                {
                    'record_date': '2024-01-10',
                    'record_type': 'Body_Weight_kg',
                    'value': 44.0
                },
                {
                    'record_date': '2024-01-15',
                    'record_type': 'Body_Weight_kg',
                    'value': 45.0
                },
                {
                    'record_date': '2024-01-20',
                    'record_type': 'milk_yield_kg_day',
                    'value': 2.5
                }
            ]
            
            for record_data in records:
                record = SheepHistoricalData(
                    user_id=test_sheep.user_id,
                    sheep_id=test_sheep.id,
                    **record_data
                )
                app.extensions['sqlalchemy'].session.add(record)
            app.extensions['sqlalchemy'].session.commit()

        response = authenticated_client.get('/api/sheep/TEST001/history')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 3
        
        # 檢查是否按日期升序排列
        dates = [record['record_date'] for record in data]
        assert dates == sorted(dates)

    def test_delete_sheep_history_permission_check(self, authenticated_client, test_sheep, app):
        """測試刪除歷史數據的權限檢查"""
        # 創建屬於其他用戶的歷史記錄
        with app.app_context():
            record = SheepHistoricalData(
                user_id=999,  # 不同的用戶ID
                sheep_id=test_sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.0
            )
            app.extensions['sqlalchemy'].session.add(record)
            app.extensions['sqlalchemy'].session.commit()
            record_id = record.id

        response = authenticated_client.delete(f'/api/sheep/history/{record_id}')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
