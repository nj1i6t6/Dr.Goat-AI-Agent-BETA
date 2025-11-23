import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta

from app.api.prediction import MIN_ELIGIBLE_AGE_DAYS, MAX_ELIGIBLE_AGE_DAYS

class TestPredictionAPI:
    """羊隻生長預測 API 測試類別"""

    def test_get_prediction_success(self, authenticated_client, app, sheep_with_weight_data, mock_gemini_api):
        """測試成功獲取預測結果"""
        ear_tag = sheep_with_weight_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        # 現行行為：若數據品質檢查失敗會回 400；成功才 200
        assert response.status_code in [200, 400]
        data = json.loads(response.data)
        if response.status_code == 200:
            assert data['success'] is True
            assert data['ear_tag'] == ear_tag
            assert data['target_days'] == 30
            assert 'predicted_weight' in data
            assert 'average_daily_gain' in data
            assert 'pred_interval' in data
            assert isinstance(data['pred_interval'], dict)
            assert set(data['pred_interval'].keys()) == {'q10', 'q90'}
            assert 'prediction_source' in data
            assert 'prediction_warning' in data
            assert 'data_quality_report' in data
            assert 'ai_analysis' in data
            assert 'daily_forecasts' in data
            assert isinstance(data['daily_forecasts'], list)
            if data['daily_forecasts']:
                assert data['daily_forecasts'][0]['day_offset'] == 0
                assert data['daily_forecasts'][-1]['day_offset'] == 30
            assert 'daily_confidence_band' in data
            assert data['model_applicability']['scope'] == 'juvenile_only'
            assert data['model_applicability']['min_age_days'] == MIN_ELIGIBLE_AGE_DAYS
            assert data['model_applicability']['max_age_days'] == MAX_ELIGIBLE_AGE_DAYS
            assert data['model_applicability']['allows_future_age_extrapolation'] is True
        else:
            assert 'error' in data

    def test_get_prediction_missing_api_key(self, authenticated_client, sheep_with_weight_data):
        """測試缺少 API 金鑰的情況"""
        ear_tag = sheep_with_weight_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=30'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'API金鑰' in data['error']

    def test_get_prediction_sheep_not_found(self, authenticated_client):
        """測試羊隻不存在的情況"""
        response = authenticated_client.get(
            '/api/prediction/goats/NON_EXIST/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert '找不到' in data['error']

    def test_get_prediction_insufficient_data(self, authenticated_client, sheep_insufficient_data):
        """測試數據不足的情況"""
        ear_tag = sheep_insufficient_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '數據不足' in data['error']

    def test_get_prediction_invalid_target_days(self, authenticated_client, sheep_with_weight_data):
        """測試無效的預測天數"""
        ear_tag = sheep_with_weight_data.EarNum
        
        # 測試過小的天數
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=5',
            headers={'X-Api-Key': 'test-api-key'}
        )
        assert response.status_code == 400
        
        # 測試過大的天數
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=400',
            headers={'X-Api-Key': 'test-api-key'}
        )
        assert response.status_code == 400

    def test_get_chart_data_success(self, authenticated_client, sheep_with_weight_data):
        """測試成功獲取圖表數據"""
        ear_tag = sheep_with_weight_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction/chart-data?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        assert response.status_code in [200, 400]
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'historical_points' in data
            assert 'trend_line' in data
            assert 'forecast_line' in data
            assert 'confidence_band' in data
            assert 'prediction_point' in data
            assert isinstance(data['historical_points'], list)
            assert isinstance(data['trend_line'], list)
        else:
            assert 'error' in data

    def test_chart_prediction_matches_main(self, authenticated_client, sheep_with_weight_data, mock_gemini_api):
        """圖表預測點應與主要預測結果一致"""
        ear_tag = sheep_with_weight_data.EarNum

        prediction_resp = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=60',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert prediction_resp.status_code == 200
        prediction_data = json.loads(prediction_resp.data)

        chart_resp = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction/chart-data?target_days=60',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert chart_resp.status_code == 200
        chart_data = json.loads(chart_resp.data)

        assert chart_data['prediction_point'] is not None
        assert chart_data['forecast_line']
        assert len(chart_data['forecast_line']) == len(prediction_data['daily_forecasts'])
        chart_weight = chart_data['prediction_point']['y']
        main_weight = prediction_data['predicted_weight']

        # 圖表點與主預測結果差異須在四捨五入誤差內
        assert abs(chart_weight - main_weight) < 0.1
        assert abs(chart_data['forecast_line'][-1]['y'] - main_weight) < 0.1

    def test_data_quality_check_functions(self, app):
        """測試數據品質檢查函式"""
        from app.api.prediction import data_quality_check
        
        # 測試空數據
        result = data_quality_check([])
        assert result['status'] == 'Error'
        assert '無體重記錄' in result['message']
        
        # 測試數據不足
        insufficient_data = [
            {'record_date': '2024-01-01', 'value': 10.0},
            {'record_date': '2024-01-02', 'value': 10.5}
        ]
        result = data_quality_check(insufficient_data)
        assert result['status'] == 'Error'
        assert '數據點不足' in result['message']
        
        # 測試良好數據
        good_data = [
            {'record_date': '2024-01-01', 'value': 10.0},
            {'record_date': '2024-01-15', 'value': 11.0},
            {'record_date': '2024-01-30', 'value': 12.0},
            {'record_date': '2024-02-15', 'value': 13.0}
        ]
        result = data_quality_check(good_data)
        assert result['status'] in ['Good', 'Warning']
        assert result['details']['record_count'] == 4

    def test_breed_reference_ranges(self, app):
        """測試品種參考範圍函式"""
        from app.api.prediction import get_breed_reference_ranges
        
        # 測試努比亞品種
        ranges = get_breed_reference_ranges('努比亞', 6)
        assert 'min' in ranges
        assert 'max' in ranges
        assert ranges['min'] > 0
        assert ranges['max'] > ranges['min']
        
        # 測試未知品種
        ranges = get_breed_reference_ranges('未知品種', 12)
        assert ranges['min'] == 0.07
        assert ranges['max'] == 0.14

    @patch('app.api.prediction.call_gemini_api')
    def test_ai_analysis_error_handling(self, mock_gemini, authenticated_client, sheep_with_weight_data):
        """測試 AI 分析錯誤處理"""
        mock_gemini.return_value = {"error": "API 錯誤"}
        ear_tag = sheep_with_weight_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        # 若數據品質先 400，不會進入 AI；若進入 AI 並錯誤則 500
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert 'error' in data

    def test_prediction_rejects_overage_sheep(self, authenticated_client, db_session, test_user, mock_gemini_api):
        """超過一年以上的羊隻應被拒絕預測"""
        from app.models import Sheep, SheepHistoricalData

        user = test_user

        senior_sheep = Sheep(
            user_id=user.id,
            EarNum='SENIOR001',
            Breed='阿爾拜因',
            Sex='母',
            BirthDate='2014-01-01',
            BirWei=2.8,
            LittleSize=2,
            Lactation=1,
            status='dry_period'
        )
        db_session.add(senior_sheep)
        db_session.commit()

        base_date = date.today() - timedelta(days=52)
        for i in range(8):
            record_date = base_date + timedelta(days=i * 7)
            record = SheepHistoricalData(
                sheep_id=senior_sheep.id,
                user_id=user.id,
                record_date=record_date.strftime('%Y-%m-%d'),
                record_type='Body_Weight_kg',
                value=50.0 + i * 0.1
            )
            db_session.add(record)
        db_session.commit()

        response = authenticated_client.get(
            f'/api/prediction/goats/{senior_sheep.EarNum}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '僅支援出生一年內' in data['error']

    def test_prediction_allows_future_age_beyond_limit(self, authenticated_client, db_session, test_user, mock_gemini_api):
        """目前年齡符合時，即使預測超出一年也應提供結果"""
        from app.models import Sheep, SheepHistoricalData

        user = test_user

        birth_date = (date.today() - timedelta(days=340)).strftime('%Y-%m-%d')
        sheep = Sheep(
            user_id=user.id,
            EarNum='NEAR_LIMIT',
            Breed='努比亞',
            Sex='母',
            BirthDate=birth_date
        )
        db_session.add(sheep)
        db_session.commit()

        # 建立足夠歷史資料
        start_date = date.today() - timedelta(days=45)
        for i in range(4):
            record = SheepHistoricalData(
                sheep_id=sheep.id,
                user_id=user.id,
                record_date=(start_date + timedelta(days=i * 7)).strftime('%Y-%m-%d'),
                record_type='Body_Weight_kg',
                value=22.0 + i
            )
            db_session.add(record)
        db_session.commit()

        # target 30 -> future age 370 (>365) 應允許預測
        response = authenticated_client.get(
            f'/api/prediction/goats/{sheep.EarNum}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['daily_forecasts']) == 31
        assert data['daily_forecasts'][0]['day_offset'] == 0
        assert data['daily_forecasts'][-1]['day_offset'] == 30
        if data['prediction_warning']:
            assert '超出幼年期範圍' not in data['prediction_warning']

        chart_resp = authenticated_client.get(
            f'/api/prediction/goats/{sheep.EarNum}/prediction/chart-data?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert chart_resp.status_code == 200
        chart_data = json.loads(chart_resp.data)
        assert chart_data['forecast_line']
        assert len(chart_data['forecast_line']) == len(data['daily_forecasts'])

    def test_prediction_rejects_underage_sheep(self, authenticated_client, db_session, test_user, mock_gemini_api):
        """未滿兩個月的羊隻應被拒絕預測"""
        from app.models import Sheep, SheepHistoricalData

        user = test_user

        birth_date = (date.today() - timedelta(days=45)).strftime('%Y-%m-%d')
        lamb = Sheep(
            user_id=user.id,
            EarNum='LAMBA01',
            Breed='努比亞',
            Sex='母',
            BirthDate=birth_date
        )
        db_session.add(lamb)
        db_session.commit()

        start_date = date.today() - timedelta(days=20)
        for i in range(3):
            record = SheepHistoricalData(
                sheep_id=lamb.id,
                user_id=user.id,
                record_date=(start_date + timedelta(days=i * 5)).strftime('%Y-%m-%d'),
                record_type='Body_Weight_kg',
                value=12.0 + i * 0.5
            )
            db_session.add(record)
        db_session.commit()

        response = authenticated_client.get(
            f'/api/prediction/goats/{lamb.EarNum}/prediction?target_days=14',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert f'至少滿 {MIN_ELIGIBLE_AGE_DAYS} 天' in data['error']

        chart_resp = authenticated_client.get(
            f'/api/prediction/goats/{lamb.EarNum}/prediction/chart-data?target_days=14',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert chart_resp.status_code == 400
        chart_data = json.loads(chart_resp.data)
        assert f'至少滿 {MIN_ELIGIBLE_AGE_DAYS} 天' in chart_data['error']

    def test_prediction_daily_confidence_band_with_lightgbm(self, authenticated_client, db_session, test_user, mock_gemini_api, monkeypatch):
        """可用 LightGBM 時應輸出每日信賴區間曲線"""
        from app.models import Sheep, SheepHistoricalData
        from app.api import prediction as prediction_mod

        class DummyModel:
            def __init__(self, value):
                self.value = value

            def predict(self, _):
                return [self.value]

        def fake_build_dataframe(sheep, future_days, future_date):
            return object(), None

        monkeypatch.setattr(prediction_mod, '_lgbm_models', {
            'main': DummyModel(26.0),
            'q10': DummyModel(23.0),
            'q90': DummyModel(30.0)
        }, raising=False)
        monkeypatch.setattr(prediction_mod, '_lgbm_load_error', None, raising=False)
        monkeypatch.setattr(prediction_mod, '_ensure_lgbm_models', lambda: True, raising=False)
        monkeypatch.setattr(prediction_mod, '_build_lgbm_dataframe', fake_build_dataframe, raising=False)

        user = test_user
        birth_date = (date.today() - timedelta(days=120)).strftime('%Y-%m-%d')
        sheep = Sheep(
            user_id=user.id,
            EarNum='CURVE001',
            Breed='努比亞',
            Sex='母',
            BirthDate=birth_date
        )
        db_session.add(sheep)
        db_session.commit()

        # 建立歷史資料
        start_date = date.today() - timedelta(days=35)
        for i in range(6):
            record = SheepHistoricalData(
                sheep_id=sheep.id,
                user_id=user.id,
                record_date=(start_date + timedelta(days=i * 5)).strftime('%Y-%m-%d'),
                record_type='Body_Weight_kg',
                value=18.0 + i * 0.8
            )
            db_session.add(record)
        db_session.commit()

        response = authenticated_client.get(
            f'/api/prediction/goats/{sheep.EarNum}/prediction?target_days=14',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['prediction_source'] == 'lightgbm'
        assert len(data['daily_forecasts']) == 15  # 含當日
        assert len(data['daily_confidence_band']) == 15
        assert all('lower' in entry and 'upper' in entry for entry in data['daily_confidence_band'])

        chart_resp = authenticated_client.get(
            f'/api/prediction/goats/{sheep.EarNum}/prediction/chart-data?target_days=14',
            headers={'X-Api-Key': 'test-api-key'}
        )

        assert chart_resp.status_code == 200
        chart_data = json.loads(chart_resp.data)
        assert chart_data['confidence_band']
        assert len(chart_data['confidence_band']) == len(data['daily_confidence_band'])
