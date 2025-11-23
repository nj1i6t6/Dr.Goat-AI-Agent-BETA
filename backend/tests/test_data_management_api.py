import pytest
import json
import io
import pandas as pd
from unittest.mock import patch
from app.models import Sheep, SheepEvent, SheepHistoricalData, ChatHistory


class TestDataManagementAPI:
    """測試數據管理 API 端點"""

    def test_export_excel_success(self, authenticated_client):
        """測試成功匯出 Excel"""
        response = authenticated_client.get('/api/data/export_excel')
        assert response.status_code == 200
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers['Content-Type']
        assert 'goat_data_export_' in response.headers['Content-Disposition']

    def test_export_excel_empty_data(self, authenticated_client):
        """測試匯出空數據"""
        response = authenticated_client.get('/api/data/export_excel')
        assert response.status_code == 200
        # 即使沒有數據，也應該能夠成功匯出空的 Excel 文件

    def test_analyze_excel_success(self, authenticated_client):
        """測試成功分析 Excel 文件"""
        # 創建模擬的 Excel 內容
        excel_content = b'\x50\x4b\x03\x04'  # 簡化的 Excel 文件標誌
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['Sheet1']
            with patch('pandas.read_excel') as mock_read:
                mock_df = type('MockDataFrame', (), {
                    'columns': ['EarNum', 'Breed', 'Sex'],
                    '__len__': lambda self: 5,
                    'head': lambda self, n: type('MockDataFrame', (), {
                        'to_dict': lambda self, orient: [
                            {'EarNum': 'TEST001', 'Breed': '波爾羊', 'Sex': '母'},
                            {'EarNum': 'TEST002', 'Breed': '努比亞', 'Sex': '公'}
                        ]
                    })(),
                    'where': lambda self, condition, other: self
                })()
                mock_read.return_value = mock_df

                data = {'file': (io.BytesIO(excel_content), 'test.xlsx')}
                response = authenticated_client.post('/api/data/analyze_excel', 
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True
                assert 'sheets' in result

    def test_analyze_excel_no_file(self, authenticated_client):
        """測試分析 Excel 沒有上傳文件"""
        response = authenticated_client.post('/api/data/analyze_excel')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_analyze_excel_empty_filename(self, authenticated_client):
        """測試分析 Excel 空文件名"""
        data = {'file': (io.BytesIO(b''), '')}
        response = authenticated_client.post('/api/data/analyze_excel', 
                                          data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result

    def test_analyze_excel_invalid_format(self, authenticated_client):
        """測試分析無效格式的文件"""
        data = {'file': (io.BytesIO(b'invalid content'), 'test.txt')}
        response = authenticated_client.post('/api/data/analyze_excel', 
                                          data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        
        result = json.loads(response.data)
        assert 'error' in result

    def test_ai_import_mapping_success(self, authenticated_client, monkeypatch):
        """測試 AI 智慧導入成功回傳映射建議"""

        class MockExcelFile:
            def __init__(self):
                self.sheet_names = ['Sheet1']

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        excel_content = b'PK\x03\x04'
        mock_df = pd.DataFrame([
            {"耳號": "TEST001", "品種": "波爾", "性別": "母"},
            {"耳號": "TEST002", "品種": "努比亞", "性別": "公"}
        ])

        monkeypatch.setattr('app.api.data_management.call_gemini_api', lambda prompt, api_key, generation_config_override=None: {
            "text": json.dumps({
                "sheets": {
                    "Sheet1": {
                        "purpose": "basic_info",
                        "confidence": 0.92,
                        "columns": {
                            "EarNum": "耳號",
                            "Breed": "品種",
                            "Sex": "性別"
                        },
                        "notes": "依據欄位名稱自動對應。"
                    }
                },
                "summary": "建議將 Sheet1 匯入為羊隻基礎資料。"
            })
        })

        with patch('pandas.ExcelFile', return_value=MockExcelFile()):
            with patch('pandas.read_excel', return_value=mock_df.where(pd.notna(mock_df), None)):
                data = {
                    'file': (io.BytesIO(excel_content), 'test.xlsx')
                }
                response = authenticated_client.post(
                    '/api/data/ai_import_mapping',
                    data=data,
                    content_type='multipart/form-data',
                    headers={'X-Api-Key': 'test-api-key'}
                )

        assert response.status_code == 200
        payload = json.loads(response.data)
        assert payload['success'] is True
        assert payload['mapping_config']['sheets']['Sheet1']['purpose'] == 'basic_info'
        assert payload['mapping_config']['sheets']['Sheet1']['columns']['EarNum'] == '耳號'

    def test_ai_import_mapping_missing_api_key(self, authenticated_client):
        """測試未配置 API 金鑰時的錯誤回應"""
        authenticated_client.application.config['GOOGLE_API_KEY'] = None

        data = {
            'file': (io.BytesIO(b'PK\x03\x04'), 'test.xlsx')
        }
        response = authenticated_client.post(
            '/api/data/ai_import_mapping',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 401
        payload = json.loads(response.data)
        assert 'error' in payload

    def test_ai_import_mapping_invalid_ai_response(self, authenticated_client, monkeypatch):
        """測試 AI 回傳非 JSON 內容時的處理"""

        class MockExcelFile:
            def __init__(self):
                self.sheet_names = ['Sheet1']

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        mock_df = pd.DataFrame([
            {"耳號": "TEST001", "品種": "波爾"}
        ])

        monkeypatch.setattr('app.api.data_management.call_gemini_api', lambda prompt, api_key, generation_config_override=None: {
            "text": "這不是 JSON"
        })

        with patch('pandas.ExcelFile', return_value=MockExcelFile()):
            with patch('pandas.read_excel', return_value=mock_df.where(pd.notna(mock_df), None)):
                data = {
                    'file': (io.BytesIO(b'PK\x03\x04'), 'test.xlsx')
                }
                response = authenticated_client.post(
                    '/api/data/ai_import_mapping',
                    data=data,
                    content_type='multipart/form-data',
                    headers={'X-Api-Key': 'test-api-key'}
                )

        assert response.status_code == 502
        payload = json.loads(response.data)
        assert 'error' in payload

    def test_process_import_no_file(self, authenticated_client):
        """測試處理導入沒有文件"""
        response = authenticated_client.post('/api/data/process_import')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_process_import_default_mode(self, authenticated_client):
        """測試預設模式導入"""
        excel_content = b'\x50\x4b\x03\x04'  # 簡化的 Excel 文件標誌
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['0009-0013A1_Basic']
            with patch('pandas.read_excel') as mock_read:
                mock_df = type('MockDataFrame', (), {
                    'iterrows': lambda self: iter([
                        (0, {'EarNum': 'TEST001', 'Breed': '1', 'Sex': '1'})
                    ]),
                    'where': lambda self, condition, other: self
                })()
                mock_read.return_value = mock_df

                data = {
                    'file': (io.BytesIO(excel_content), 'test.xlsx'),
                    'is_default_mode': 'true'
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True

    def test_process_import_manual_mode_no_config(self, authenticated_client):
        """測試手動模式沒有配置"""
        excel_content = b'\x50\x4b\x03\x04'
        
        data = {
            'file': (io.BytesIO(excel_content), 'test.xlsx'),
            'is_default_mode': 'false'
        }
        response = authenticated_client.post('/api/data/process_import',
                                          data=data, content_type='multipart/form-data')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result

    def test_process_import_invalid_config(self, authenticated_client):
        """測試手動模式無效配置"""
        excel_content = b'\x50\x4b\x03\x04'
        
        data = {
            'file': (io.BytesIO(excel_content), 'test.xlsx'),
            'is_default_mode': 'false',
            'mapping_config': 'invalid json'
        }
        response = authenticated_client.post('/api/data/process_import',
                                          data=data, content_type='multipart/form-data')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result

    def test_process_import_manual_mode_with_config(self, authenticated_client):
        """測試手動模式有效配置"""
        excel_content = b'\x50\x4b\x03\x04'
        
        config = {
            "sheets": {
                "Sheet1": {
                    "purpose": "basic_info",
                    "columns": {
                        "EarNum": "EarNum",
                        "Breed": "Breed",
                        "Sex": "Sex"
                    }
                }
            }
        }
        
        with patch('pandas.ExcelFile') as mock_excel:
            mock_excel.return_value.sheet_names = ['Sheet1']
            with patch('pandas.read_excel') as mock_read:
                mock_df = type('MockDataFrame', (), {
                    'iterrows': lambda self: iter([
                        (0, {'EarNum': 'TEST001', 'Breed': '波爾羊', 'Sex': '母'})
                    ]),
                    'where': lambda self, condition, other: self
                })()
                mock_read.return_value = mock_df

                data = {
                    'file': (io.BytesIO(excel_content), 'test.xlsx'),
                    'is_default_mode': 'false',
                    'mapping_config': json.dumps(config)
                }
                response = authenticated_client.post('/api/data/process_import',
                                                  data=data, content_type='multipart/form-data')
                
                assert response.status_code == 200
                result = json.loads(response.data)
                assert result['success'] is True

    def test_data_management_unauthenticated_access(self, client):
        """測試未認證用戶訪問數據管理 API"""
        endpoints = [
            '/api/data/export_excel',
            '/api/data/analyze_excel',
            '/api/data/ai_import_mapping',
            '/api/data/process_import'
        ]
        
        for endpoint in endpoints:
            if endpoint == '/api/data/export_excel':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            assert response.status_code == 401  # 應該返回未授權
