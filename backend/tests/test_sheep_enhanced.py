"""
增強的山羊管理API測試
專門用於提高sheep.py的測試覆蓋率
"""

import pytest
import json
from unittest.mock import patch
from app.models import Sheep, SheepEvent, SheepHistoricalData
from datetime import datetime, date


class TestSheepAPIEnhanced:
    """增強的山羊API測試類別"""

    def test_add_sheep_non_json_request(self, authenticated_client):
        """測試非JSON格式的新增羊隻請求"""
        response = authenticated_client.post('/api/sheep/', 
                                           data='not json', 
                                           content_type='text/plain')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_add_sheep_database_error(self, authenticated_client, mocker):
        """測試新增羊隻時資料庫錯誤"""
        sheep_data = {
            'EarNum': 'ERROR001',
            'Breed': '波爾羊',
            'Sex': '母'
        }
        
        # 模擬資料庫提交失敗
        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.post('/api/sheep/', json=sheep_data)
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_update_sheep_non_json_request(self, authenticated_client, test_sheep):
        """測試非JSON格式的更新羊隻請求"""
        response = authenticated_client.put('/api/sheep/TEST001',
                                          data='not json',
                                          content_type='text/plain')
        assert response.status_code == 415  # Flask 在沒有適當 Content-Type 時返回 415

    def test_update_sheep_with_historical_data_recording(self, authenticated_client, test_sheep, app):
        """測試更新羊隻時記錄歷史數據"""
        update_data = {
            'Body_Weight_kg': 50.0,
            'milk_yield_kg_day': 2.5,
            'milk_fat_percentage': 3.8,
            'record_date': '2024-01-15'
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        assert response.status_code == 200
        
        # 檢查歷史數據是否被記錄
        with app.app_context():
            history_records = SheepHistoricalData.query.filter_by(sheep_id=test_sheep.id).all()
            assert len(history_records) >= 1

    def test_update_sheep_with_empty_values(self, authenticated_client, test_sheep):
        """測試使用空值更新羊隻"""
        update_data = {
            'status': '',  # 空字串應該被轉換為None
            'notes': '',
            'Body_Weight_kg': 48.0
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_update_sheep_with_invalid_date_format(self, authenticated_client, test_sheep, app):
        """測試使用無效日期格式更新羊隻"""
        update_data = {
            'Body_Weight_kg': 47.0,
            'record_date': 'invalid-date-format'
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        # 應該成功，但不會記錄歷史數據（因為日期格式無效）
        assert response.status_code == 200

    def test_update_sheep_database_error(self, authenticated_client, test_sheep):
        """測試更新羊隻時資料庫錯誤"""
        update_data = {
            'Body_Weight_kg': 49.0
        }
        
        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_delete_sheep_database_error(self, authenticated_client, test_sheep):
        """測試刪除羊隻時資料庫錯誤"""
        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.delete('/api/sheep/TEST001')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_get_sheep_events_with_ordering(self, authenticated_client, test_sheep, app):
        """測試獲取山羊事件並檢查排序"""
        with app.app_context():
            # 創建多個事件，測試排序
            events_data = [
                {'event_date': '2024-01-10', 'event_type': '第一個事件'},
                {'event_date': '2024-01-15', 'event_type': '第二個事件'},
                {'event_date': '2024-01-15', 'event_type': '同日第二個事件'}  # 同一天的事件測試ID排序
            ]
            
            for event_data in events_data:
                event = SheepEvent(
                    user_id=test_sheep.user_id,
                    sheep_id=test_sheep.id,
                    **event_data
                )
                app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()

        response = authenticated_client.get('/api/sheep/TEST001/events')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 3
        # 檢查是否按日期降序排列
        dates = [event['event_date'] for event in data]
        assert dates == sorted(dates, reverse=True)

    def test_add_sheep_event_non_json_request(self, authenticated_client, test_sheep):
        """測試非JSON格式的新增事件請求"""
        response = authenticated_client.post('/api/sheep/TEST001/events',
                                           data='not json',
                                           content_type='text/plain')
        assert response.status_code == 415  # Unsupported Media Type

    def test_add_sheep_event_database_error(self, authenticated_client, test_sheep):
        """測試新增事件時資料庫錯誤"""
        event_data = {
            'event_date': '2024-01-15',
            'event_type': '測試事件',
            'description': '測試描述'
        }
        
        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.post('/api/sheep/TEST001/events', json=event_data)
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_update_event_validation(self, authenticated_client, test_sheep, app):
        """測試更新事件的資料驗證"""
        # 先創建一個事件
        with app.app_context():
            event = SheepEvent(
                user_id=test_sheep.user_id,
                sheep_id=test_sheep.id,
                event_date='2024-01-15',
                event_type='原始事件'
            )
            app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()
            event_id = event.id

        # 測試缺少必填欄位
        response = authenticated_client.put(f'/api/sheep/events/{event_id}', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

        # 測試缺少事件日期
        response = authenticated_client.put(f'/api/sheep/events/{event_id}', 
                                          json={'event_type': '更新事件'})
        assert response.status_code == 400

        # 測試缺少事件類型
        response = authenticated_client.put(f'/api/sheep/events/{event_id}', 
                                          json={'event_date': '2024-01-16'})
        assert response.status_code == 400

    def test_update_event_permission_check(self, authenticated_client, test_sheep, app, test_user):
        """測試更新事件的權限檢查"""
        # 創建屬於其他用戶的事件
        with app.app_context():
            event = SheepEvent(
                user_id=999,  # 不同的用戶ID
                sheep_id=test_sheep.id,
                event_date='2024-01-15',
                event_type='其他用戶事件'
            )
            app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()
            event_id = event.id

        update_data = {
            'event_date': '2024-01-16',
            'event_type': '嘗試更新'
        }
        
        response = authenticated_client.put(f'/api/sheep/events/{event_id}', json=update_data)
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data

    def test_update_event_database_error(self, authenticated_client, test_sheep, app):
        """測試更新事件時資料庫錯誤"""
        # 先創建一個事件
        with app.app_context():
            event = SheepEvent(
                user_id=test_sheep.user_id,
                sheep_id=test_sheep.id,
                event_date='2024-01-15',
                event_type='測試事件'
            )
            app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()
            event_id = event.id

        update_data = {
            'event_date': '2024-01-16',
            'event_type': '更新事件'
        }
        
        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.put(f'/api/sheep/events/{event_id}', json=update_data)
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_delete_event_permission_check(self, authenticated_client, test_sheep, app):
        """測試刪除事件的權限檢查"""
        # 創建屬於其他用戶的事件
        with app.app_context():
            event = SheepEvent(
                user_id=999,  # 不同的用戶ID
                sheep_id=test_sheep.id,
                event_date='2024-01-15',
                event_type='其他用戶事件'
            )
            app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()
            event_id = event.id

        response = authenticated_client.delete(f'/api/sheep/events/{event_id}')
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data

    def test_delete_event_database_error(self, authenticated_client, test_sheep, app):
        """測試刪除事件時資料庫錯誤"""
        # 先創建一個事件
        with app.app_context():
            event = SheepEvent(
                user_id=test_sheep.user_id,
                sheep_id=test_sheep.id,
                event_date='2024-01-15',
                event_type='測試事件'
            )
            app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()
            event_id = event.id

        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.delete(f'/api/sheep/events/{event_id}')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_get_sheep_history_with_ordering(self, authenticated_client, test_sheep, app):
        """測試獲取山羊歷史數據並檢查排序"""
        with app.app_context():
            # 創建多個歷史記錄，測試排序
            history_data = [
                {'record_date': '2024-01-10', 'record_type': 'Body_Weight_kg', 'value': 45.0},
                {'record_date': '2024-01-05', 'record_type': 'Body_Weight_kg', 'value': 44.0},
                {'record_date': '2024-01-15', 'record_type': 'milk_yield_kg_day', 'value': 2.5}
            ]
            
            for data in history_data:
                record = SheepHistoricalData(
                    user_id=test_sheep.user_id,
                    sheep_id=test_sheep.id,
                    **data
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

    def test_delete_sheep_history_database_error(self, authenticated_client, test_sheep, app):
        """測試刪除歷史數據時資料庫錯誤"""
        # 先創建一個歷史記錄
        with app.app_context():
            record = SheepHistoricalData(
                user_id=test_sheep.user_id,
                sheep_id=test_sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.0
            )
            app.extensions['sqlalchemy'].session.add(record)
            app.extensions['sqlalchemy'].session.commit()
            record_id = record.id

        with patch('app.models.db.session.commit', side_effect=Exception("Database error")):
            response = authenticated_client.delete(f'/api/sheep/history/{record_id}')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_update_sheep_with_all_historical_fields(self, authenticated_client, test_sheep, app):
        """測試更新包含所有歷史欄位的羊隻數據"""
        update_data = {
            'Body_Weight_kg': 52.0,
            'milk_yield_kg_day': 3.0,
            'milk_fat_percentage': 4.2,
            'status': '泌乳中',
            'notes': '健康狀況良好',
            'record_date': '2024-01-20'
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # 檢查歷史數據是否正確記錄
        with app.app_context():
            history_records = SheepHistoricalData.query.filter_by(sheep_id=test_sheep.id).all()
            # 應該有3條歷史記錄（3個歷史欄位）
            assert len(history_records) >= 3

    def test_update_sheep_exclude_unset_fields(self, authenticated_client, test_sheep):
        """測試更新羊隻時排除未設置的欄位"""
        # 只更新一個欄位
        update_data = {
            'status': '健康'
        }
        
        response = authenticated_client.put('/api/sheep/TEST001', json=update_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # 其他欄位應該保持不變

    def test_sheep_events_route_errors(self, authenticated_client):
        """測試山羊事件路由錯誤處理"""
        # 測試不存在的山羊
        response = authenticated_client.get('/api/sheep/NOTFOUND/events')
        assert response.status_code == 404

        # 測試為不存在的山羊添加事件
        event_data = {
            'event_date': '2024-01-15',
            'event_type': '測試事件'
        }
        response = authenticated_client.post('/api/sheep/NOTFOUND/events', json=event_data)
        assert response.status_code == 404

    def test_sheep_history_route_errors(self, authenticated_client):
        """測試山羊歷史數據路由錯誤處理"""
        # 測試不存在的山羊
        response = authenticated_client.get('/api/sheep/NOTFOUND/history')
        assert response.status_code == 404
