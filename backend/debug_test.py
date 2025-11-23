"""
簡單的測試腳本來調試 500 錯誤
"""
import os
import tempfile
import sys
sys.path.append('.')

os.environ.setdefault('DOTENV_PATH', 'NON_EXISTENT_.env')
os.environ.setdefault('API_HMAC_SECRET', 'debug-hmac-secret-value-should-be-32-bytes')

from app import create_app, db

# 設置測試環境
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['CORS_ORIGINS'] = '*'
for key in ['DB_USERNAME', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']:
    if key in os.environ:
        del os.environ[key]

# 創建測試應用
db_fd, db_path = tempfile.mkstemp(suffix='.db')
os.close(db_fd)

app = create_app()
app.config.update({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
    'SECRET_KEY': 'test-secret-key'
})

with app.app_context():
    db.create_all()
    
    # 創建測試客戶端
    client = app.test_client()
    
    # 測試 API 端點
    response = client.get('/api/agent/tip', headers={'X-Api-Key': 'test-key'})
    
    print(f"狀態碼: {response.status_code}")
    print(f"響應內容: {response.get_data(as_text=True)}")
    
    if response.status_code != 200:
        # 檢查應用日誌
        import traceback
        with app.test_request_context('/api/agent/tip', headers={'X-Api-Key': 'test-key'}):
            try:
                from app.api.agent import agent_bp
                print("Blueprint 導入成功")
            except Exception as e:
                print(f"Blueprint 導入錯誤: {e}")
                traceback.print_exc()

# 清理
try:
    os.unlink(db_path)
except:
    pass
