"""
增強的資料管理API測試
專門用於提高data_management.py的測試覆蓋率
"""

import pytest
import json
import io
from unittest.mock import patch, MagicMock
import pandas as pd
from app.models import Sheep, SheepEvent, SheepHistoricalData, ChatHistory
from datetime import datetime, date


class TestDataManagementEnhanced:
    """增強的資料管理API測試類別"""

    def test_export_excel_with_all_data_types(self, authenticated_client, app, test_user):
        """測試匯出包含所有資料類型的Excel"""
        with app.app_context():
            # 創建完整的測試數據
            sheep = Sheep(
                user_id=test_user.id,
                EarNum='EXPORT001',
                Breed='波爾羊',
                Sex='母',
                Body_Weight_kg=45.5
            )
            app.extensions['sqlalchemy'].session.add(sheep)
            app.extensions['sqlalchemy'].session.commit()

            # 添加事件記錄
            event = SheepEvent(
                user_id=test_user.id,
                sheep_id=sheep.id,
                event_date='2024-01-15',
                event_type='疫苗接種',
                description='接種測試疫苗'
            )
            app.extensions['sqlalchemy'].session.add(event)

            # 添加歷史數據
            history = SheepHistoricalData(
                user_id=test_user.id,
                sheep_id=sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.5,
                notes='定期稱重'
            )
            app.extensions['sqlalchemy'].session.add(history)

            # 添加聊天記錄
            chat = ChatHistory(
                user_id=test_user.id,
                session_id='test-session',
                role='user',
                content='測試問題',
                timestamp=datetime.now()
            )
            app.extensions['sqlalchemy'].session.add(chat)
            app.extensions['sqlalchemy'].session.commit()

            # 執行匯出
            response = authenticated_client.get('/api/data/export_excel')
            assert response.status_code == 200
            assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers['Content-Type']

    def test_export_excel_exception_handling(self, authenticated_client, mocker):
        """測試匯出Excel時的異常處理"""
        # 模擬資料庫查詢失敗
        with patch('app.models.Sheep.query') as mock_query:
            mock_query.filter_by.side_effect = Exception("Database error")
            
            response = authenticated_client.get('/api/data/export_excel')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_analyze_excel_with_multiple_sheets(self, authenticated_client):
        """測試分析包含多個工作表的Excel文件"""
        excel_content = b'\x50\x4b\x03\x04'  # Excel文件標誌
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['基本資料', '事件記錄', '歷史數據']
            
            # 模擬不同工作表的數據
            def mock_read_excel(xls, sheet_name, dtype):
                df = MagicMock()
                if sheet_name == '基本資料':
                    df.columns = ['EarNum', 'Breed', 'Sex']
                    df.__len__ = lambda self: 10
                    df.head = lambda n: MagicMock(
                        to_dict=lambda orient: [
                            {'EarNum': 'MULTI001', 'Breed': '波爾羊', 'Sex': '母'},
                            {'EarNum': 'MULTI002', 'Breed': '努比亞', 'Sex': '公'}
                        ]
                    )
                    df.where = lambda condition, other=None: df
                    return df
                elif sheet_name == '事件記錄':
                    df.columns = ['EarNum', 'EventDate', 'EventType']
                    df.__len__ = lambda self: 5
                    df.head = lambda n: MagicMock(
                        to_dict=lambda orient: [
                            {'EarNum': 'MULTI001', 'EventDate': '2024-01-15', 'EventType': '疫苗接種'}
                        ]
                    )
                    df.where = lambda condition, other=None: df
                    return df
                else:  # 歷史數據
                    df.columns = ['EarNum', 'RecordDate', 'RecordType', 'Value']
                    df.__len__ = lambda self: 3
                    df.head = lambda n: MagicMock(
                        to_dict=lambda orient: [
                            {'EarNum': 'MULTI001', 'RecordDate': '2024-01-15', 'RecordType': 'Body_Weight_kg', 'Value': '45.5'}
                        ]
                    )
                    df.where = lambda condition, other=None: df
                    return df
            
            with patch('pandas.read_excel', side_effect=mock_read_excel):
                data = {'file': (io.BytesIO(excel_content), 'multi_sheet.xlsx')}
                response = authenticated_client.post('/api/data/analyze_excel', 
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True
                assert len(result['sheets']) == 3

    def test_analyze_excel_exception_handling(self, authenticated_client):
        """測試分析Excel時的異常處理"""
        excel_content = b'\x50\x4b\x03\x04'
        
        with patch('pandas.ExcelFile', side_effect=Exception("Excel parsing error")):
            data = {'file': (io.BytesIO(excel_content), 'error.xlsx')}
            response = authenticated_client.post('/api/data/analyze_excel', 
                                              data=data, content_type='multipart/form-data')
            
            assert response.status_code == 500
            result = json.loads(response.data)
            assert 'error' in result

    def test_process_import_with_breed_and_sex_mapping(self, authenticated_client, app, test_user):
        """測試使用品種和性別映射的導入"""
        excel_content = b'\x50\x4b\x03\x04'
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['S2_Breed', 'S7_Sex', '0009-0013A1_Basic']
            
            def mock_read_excel(xls, sheet_name, dtype):
                df = MagicMock()
                df.where = lambda condition, other=None: df
                
                if sheet_name == 'S2_Breed':
                    df.iterrows.return_value = [
                        (0, {'Code': '1', 'Name': '波爾羊'}),
                        (1, {'Code': '2', 'Name': '努比亞羊'})
                    ]
                elif sheet_name == 'S7_Sex':
                    df.iterrows.return_value = [
                        (0, {'Code': '1', 'Name': '母'}),
                        (1, {'Code': '2', 'Name': '公'})
                    ]
                else:  # 基本資料
                    df.iterrows.return_value = [
                        (0, {'EarNum': 'MAP001', 'Breed': '1', 'Sex': '1', 'BirthDate': '2023-01-15'})
                    ]
                return df
            
            with patch('pandas.read_excel', side_effect=mock_read_excel):
                data = {
                    'file': (io.BytesIO(excel_content), 'mapping_test.xlsx'),
                    'is_default_mode': 'true'
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True

    def test_process_import_with_various_record_types(self, authenticated_client, app, test_user):
        """測試導入各種記錄類型"""
        excel_content = b'\x50\x4b\x03\x04'
        
        # 先創建基礎羊隻
        with app.app_context():
            sheep = Sheep(
                user_id=test_user.id,
                EarNum='RECORD001',
                Breed='波爾羊',
                Sex='母'
            )
            app.extensions['sqlalchemy'].session.add(sheep)
            app.extensions['sqlalchemy'].session.commit()
        
        config = {
            "sheets": {
                "0009-0013A4_Kidding": {
                    "purpose": "kidding_record",
                    "columns": {"EarNum": "EarNum", "YeanDate": "YeanDate", "KidNum": "KidNum"}
                },
                "0009-0013A2_PubMat": {
                    "purpose": "mating_record", 
                    "columns": {"EarNum": "EarNum", "Mat_date": "Mat_date", "Mat_grouM_Sire": "Mat_grouM_Sire"}
                },
                "0009-0013A3_Yean": {
                    "purpose": "yean_record",
                    "columns": {"EarNum": "EarNum", "YeanDate": "YeanDate", "DryOffDate": "DryOffDate", "Lactation": "Lactation"}
                },
                "0009-0013A9_Milk": {
                    "purpose": "milk_yield_record",
                    "columns": {"EarNum": "EarNum", "MeaDate": "MeaDate", "Milk": "Milk"}
                },
                "0009-0013A11_MilkAnalysis": {
                    "purpose": "milk_analysis_record",
                    "columns": {"EarNum": "EarNum", "MeaDate": "MeaDate", "AMFat": "AMFat"}
                }
            }
        }
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = list(config["sheets"].keys())
            
            def mock_read_excel(xls, sheet_name, dtype):
                df = MagicMock()
                df.where = lambda condition, other: df
                
                if sheet_name == "0009-0013A4_Kidding":
                    df.iterrows.return_value = [
                        (0, {'EarNum': 'RECORD001', 'YeanDate': '2024-01-15', 'KidNum': '2'})
                    ]
                elif sheet_name == "0009-0013A2_PubMat":
                    df.iterrows.return_value = [
                        (0, {'EarNum': 'RECORD001', 'Mat_date': '2023-12-01', 'Mat_grouM_Sire': 'SIRE001'})
                    ]
                elif sheet_name == "0009-0013A3_Yean":
                    df.iterrows.return_value = [
                        (0, {'EarNum': 'RECORD001', 'YeanDate': '2024-01-15', 'DryOffDate': '2024-06-15', 'Lactation': '1'})
                    ]
                elif sheet_name == "0009-0013A9_Milk":
                    df.iterrows.return_value = [
                        (0, {'EarNum': 'RECORD001', 'MeaDate': '2024-02-01', 'Milk': '2.5'})
                    ]
                elif sheet_name == "0009-0013A11_MilkAnalysis":
                    df.iterrows.return_value = [
                        (0, {'EarNum': 'RECORD001', 'MeaDate': '2024-02-01', 'AMFat': '3.8'})
                    ]
                else:
                    df.iterrows.return_value = []
                
                return df
            
            with patch('pandas.read_excel', side_effect=mock_read_excel):
                data = {
                    'file': (io.BytesIO(excel_content), 'records_test.xlsx'),
                    'is_default_mode': 'false',
                    'mapping_config': json.dumps(config)
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True

    def test_process_import_with_invalid_dates(self, authenticated_client, app, test_user):
        """測試導入包含無效日期的數據"""
        excel_content = b'\x50\x4b\x03\x04'
        
        # 先創建基礎羊隻
        with app.app_context():
            sheep = Sheep(
                user_id=test_user.id,
                EarNum='INVALID001',
                Breed='波爾羊',
                Sex='母'
            )
            app.extensions['sqlalchemy'].session.add(sheep)
            app.extensions['sqlalchemy'].session.commit()
        
        config = {
            "sheets": {
                "Events": {
                    "purpose": "kidding_record",
                    "columns": {"EarNum": "EarNum", "YeanDate": "YeanDate"}
                }
            }
        }
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['Events']
            
            def mock_read_excel(xls, sheet_name, dtype):
                df = MagicMock()
                df.where = lambda condition, other: df
                df.iterrows.return_value = [
                    (0, {'EarNum': 'INVALID001', 'YeanDate': '1900-01-01'}),  # 無效日期
                    (1, {'EarNum': 'INVALID001', 'YeanDate': 'invalid-date'}),  # 無效格式
                    (2, {'EarNum': 'INVALID001', 'YeanDate': None})  # 空值
                ]
                return df
            
            with patch('pandas.read_excel', side_effect=mock_read_excel):
                data = {
                    'file': (io.BytesIO(excel_content), 'invalid_dates.xlsx'),
                    'is_default_mode': 'false',
                    'mapping_config': json.dumps(config)
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                # 應該仍然成功，但會跳過無效的記錄
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True

    def test_process_import_rollback_on_error(self, authenticated_client, app, test_user):
        """測試導入過程中發生錯誤時的回滾"""
        excel_content = b'\x50\x4b\x03\x04'
        
        config = {
            "sheets": {
                "Test": {
                    "purpose": "basic_info",
                    "columns": {"EarNum": "EarNum", "Breed": "Breed"}
                }
            }
        }
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['Test']
            
            with patch('pandas.read_excel') as mock_read:
                # 模擬pandas讀取Excel時發生異常
                mock_read.side_effect = Exception("Pandas error")
                
                data = {
                    'file': (io.BytesIO(excel_content), 'error_test.xlsx'),
                    'is_default_mode': 'false',
                    'mapping_config': json.dumps(config)
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 500
                result = json.loads(response.data)
                assert 'error' in result

    def test_process_import_with_empty_ear_num(self, authenticated_client):
        """測試導入包含空耳號的數據"""
        excel_content = b'\x50\x4b\x03\x04'
        
        config = {
            "sheets": {
                "Test": {
                    "purpose": "basic_info",
                    "columns": {"EarNum": "EarNum", "Breed": "Breed"}
                }
            }
        }
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['Test']
            
            def mock_read_excel(xls, sheet_name, dtype):
                df = MagicMock()
                df.where = lambda condition, other: df
                df.iterrows.return_value = [
                    (0, {'EarNum': None, 'Breed': '波爾羊'}),  # 空耳號
                    (1, {'EarNum': '', 'Breed': '努比亞羊'}),   # 空字串耳號
                    (2, {'EarNum': 'VALID001', 'Breed': '台灣黑山羊'})  # 正常耳號
                ]
                return df
            
            with patch('pandas.read_excel', side_effect=mock_read_excel):
                data = {
                    'file': (io.BytesIO(excel_content), 'empty_earnum.xlsx'),
                    'is_default_mode': 'false',
                    'mapping_config': json.dumps(config)
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True

    def test_process_import_ignore_sheets(self, authenticated_client):
        """測試導入時忽略某些工作表"""
        excel_content = b'\x50\x4b\x03\x04'
        
        config = {
            "sheets": {
                "Ignore1": {"purpose": "ignore"},
                "Basic": {
                    "purpose": "basic_info",
                    "columns": {"EarNum": "EarNum", "Breed": "Breed"}
                },
                "Ignore2": {"purpose": "ignore"}
            }
        }
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['Ignore1', 'Basic', 'Ignore2']
            
            def mock_read_excel(xls, sheet_name, dtype):
                df = MagicMock()
                df.where = lambda condition, other: df
                if sheet_name == 'Basic':
                    df.iterrows.return_value = [
                        (0, {'EarNum': 'IGNORE001', 'Breed': '波爾羊'})
                    ]
                else:
                    df.iterrows.return_value = []
                return df
            
            with patch('pandas.read_excel', side_effect=mock_read_excel):
                data = {
                    'file': (io.BytesIO(excel_content), 'ignore_test.xlsx'),
                    'is_default_mode': 'false',
                    'mapping_config': json.dumps(config)
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True

    def test_export_excel_with_missing_sheep_map(self, authenticated_client, app, test_user):
        """測試匯出時缺少羊隻映射的情況"""
        with app.app_context():
            # 創建事件但不創建對應的羊隻（模擬資料不一致的情況）
            event = SheepEvent(
                user_id=test_user.id,
                sheep_id=9999,  # 不存在的羊隻ID
                event_date='2024-01-15',
                event_type='測試事件',
                description='測試描述'
            )
            app.extensions['sqlalchemy'].session.add(event)
            app.extensions['sqlalchemy'].session.commit()

            response = authenticated_client.get('/api/data/export_excel')
            # 應該仍然成功，但會跳過無效的記錄
            assert response.status_code == 200
