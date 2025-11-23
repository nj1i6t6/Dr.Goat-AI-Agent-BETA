"""
測試配置和共用 fixtures
"""

import pytest
import tempfile
import os
from datetime import date, timedelta
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """創建測試應用實例"""
    # 設置測試環境變數
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['CORS_ORIGINS'] = '*'
    os.environ['GOOGLE_API_KEY'] = 'test-gemini-api-key'
    os.environ['USE_FAKE_REDIS_FOR_TESTS'] = '1'
    os.environ['API_HMAC_SECRET'] = 'test-hmac-secret-value-should-be-32+'
    # 清除資料庫相關環境變數，確保使用 SQLite，並避免載入專案根 .env
    for key in [
        'DB_USERNAME', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME',
        'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB'
    ]:
        os.environ.pop(key, None)
    for key in ['REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD']:
        os.environ.pop(key, None)
    # 阻止 app/__init__.py 在匯入時載入專案根 .env
    os.environ['DOTENV_PATH'] = 'NON_EXISTENT_.env'
    
    # 創建臨時資料庫文件
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # 立即關閉，讓 SQLite 可以使用
    
    # 延後匯入，確保先完成環境變數清理
    from app import create_app, db
    # 設置測試配置
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        # 清理臨時文件
        db.drop_all()
    
    # 刪除臨時文件
    try:
        os.unlink(db_path)
    except OSError:
        pass  # 文件可能已經被刪除


@pytest.fixture
def client(app):
    """創建測試客戶端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """創建測試命令行運行器"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """創建測試用戶"""
    from app import db
    from app.models import User
    with app.app_context():
        # 清理現有用戶（如果存在）
        existing_user = User.query.filter_by(username='testuser').first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        
        user = User(
            username='testuser',
            password_hash=generate_password_hash('testpass')
        )
        db.session.add(user)
        db.session.commit()
        
        # 刷新對象以避免 DetachedInstanceError
        db.session.refresh(user)
        # 將對象從會話中分離，但保留其狀態
        db.session.expunge(user)
        return user


@pytest.fixture
def authenticated_client(client, test_user):
    """創建已認證的測試客戶端"""
    # 登入測試用戶
    client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    return client


@pytest.fixture
def test_sheep_data():
    """測試羊隻資料"""
    return {
        'EarNum': 'TEST001',
        'Breed': '波爾羊',
        'Sex': '母',
        'BirthDate': '2023-01-15',
        'Body_Weight_kg': 45.5,
        'Age_Months': 12,
        'status': '懷孕',
        'FarmNum': 'F001'
    }


@pytest.fixture
def test_sheep(app, test_user, test_sheep_data):
    """創建測試羊隻"""
    from app import db
    from app.models import User, Sheep
    with app.app_context():
        # 重新獲取用戶以確保在當前會話中
        user = User.query.filter_by(username='testuser').first()
        sheep = Sheep(user_id=user.id, **test_sheep_data)
        db.session.add(sheep)
        db.session.commit()
        
        # 刷新對象以避免 DetachedInstanceError
        db.session.refresh(sheep)
        # 將對象從會話中分離，但保留其狀態
        db.session.expunge(sheep)
        return sheep


@pytest.fixture
def multiple_test_sheep(app, test_user):
    """創建多隻測試羊隻"""
    from app import db
    from app.models import User, Sheep
    with app.app_context():
        sheep_data = [
            {
                'EarNum': 'A001',
                'Breed': '波爾羊',
                'Sex': '母',
                'Body_Weight_kg': 45.0,
                'FarmNum': 'F001'
            },
            {
                'EarNum': 'A002', 
                'Breed': '台灣黑山羊',
                'Sex': '公',
                'Body_Weight_kg': 55.0,
                'FarmNum': 'F001'
            },
            {
                'EarNum': 'B001',
                'Breed': '努比亞羊',
                'Sex': '母',
                'Body_Weight_kg': 40.0,
                'FarmNum': 'F002'
            }
        ]
        
        # 重新獲取用戶以確保在當前會話中
        user = User.query.filter_by(username='testuser').first()
        sheep_list = []
        for data in sheep_data:
            sheep = Sheep(user_id=user.id, **data)
            db.session.add(sheep)
            sheep_list.append(sheep)
        
        db.session.commit()
        
        # 刷新並分離所有對象
        for sheep in sheep_list:
            db.session.refresh(sheep)
            db.session.expunge(sheep)
        
        return sheep_list


@pytest.fixture
def mock_gemini_api(monkeypatch):
    """模擬 Gemini API 調用"""
    def mock_call_gemini_api(prompt, api_key, generation_config_override=None, safety_settings_override=None):
        return {
            "text": "這是模擬的 AI 回應內容。根據您提供的羊隻資料，建議每日飼料需求如下：\n\n- DMI: 1.2-1.5 kg/day\n- ME: 8.5-9.5 MJ/day\n- CP: 120-140 g/day"
        }
    
    # 嘗試多個可能的路徑
    monkeypatch.setattr('app.utils.call_gemini_api', mock_call_gemini_api)
    monkeypatch.setattr('app.api.agent.call_gemini_api', mock_call_gemini_api)
    monkeypatch.setattr('app.api.prediction.call_gemini_api', mock_call_gemini_api)
    monkeypatch.setattr('app.api.data_management.call_gemini_api', mock_call_gemini_api)
    monkeypatch.setattr('app.api.agent.rag_query', lambda *args, **kwargs: [])
    return mock_call_gemini_api


@pytest.fixture
def mock_gemini_api_error(monkeypatch):
    """模擬 Gemini API 錯誤"""
    def mock_call_gemini_api_error(prompt, api_key, generation_config_override=None):
        return {"error": "API 調用失敗"}
    
    monkeypatch.setattr('app.utils.call_gemini_api', mock_call_gemini_api_error)
    monkeypatch.setattr('app.api.prediction.call_gemini_api', mock_call_gemini_api_error)
    monkeypatch.setattr('app.api.data_management.call_gemini_api', mock_call_gemini_api_error)
    monkeypatch.setattr('app.api.agent.rag_query', lambda *args, **kwargs: [])
    return mock_call_gemini_api_error


@pytest.fixture
def sheep_with_weight_data(authenticated_client, db_session):
    """創建帶有足夠體重數據的羊隻 fixture"""
    from app.models import Sheep, SheepHistoricalData, User
    
    user = User.query.filter_by(username='testuser').first()
    
    # 創建羊隻
    birth_date = date.today() - timedelta(days=180)
    sheep = Sheep(
        user_id=user.id,
        EarNum='PRED001',
        Breed='努比亞',
        Sex='母',
        BirthDate=birth_date.strftime('%Y-%m-%d')
    )
    db_session.add(sheep)
    db_session.commit()
    
    # 創建足夠的體重歷史記錄
    start_record_date = date.today() - timedelta(days=75)
    for i in range(6):  # 6 筆記錄，滿足最少3筆的要求
        record = SheepHistoricalData(
            sheep_id=sheep.id,
            user_id=user.id,
            record_date=(start_record_date + timedelta(days=i * 15)).strftime('%Y-%m-%d'),
            record_type='Body_Weight_kg',
            value=18.0 + i * 1.5  # 模擬增長趨勢
        )
        db_session.add(record)
    
    db_session.commit()
    return sheep


@pytest.fixture
def sheep_insufficient_data(authenticated_client, db_session):
    """創建數據不足的羊隻 fixture"""
    from app.models import Sheep, SheepHistoricalData, User
    
    user = User.query.filter_by(username='testuser').first()
    
    # 創建羊隻
    birth_date = date.today() - timedelta(days=120)
    sheep = Sheep(
        user_id=user.id,
        EarNum='INSUFFICIENT001',
        Breed='波爾',
        Sex='公',
        BirthDate=birth_date.strftime('%Y-%m-%d')
    )
    db_session.add(sheep)
    db_session.commit()
    
    # 只創建1筆記錄，不足以進行預測
    record = SheepHistoricalData(
        sheep_id=sheep.id,
        user_id=user.id,
        record_date=(date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
        record_type='Body_Weight_kg',
        value=15.0
    )
    db_session.add(record)
    db_session.commit()
    return sheep


@pytest.fixture
def db_session(app):
    """提供資料庫會話的fixture"""
    from app import db
    with app.app_context():
        return db.session

