"""
測試認證過程
"""
import os
import tempfile
import sys
sys.path.append('.')

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

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
    
    # 檢查測試用戶是否已存在，不存在才創建
    existing_user = User.query.filter_by(username='testuser').first()
    if not existing_user:
        user = User(
            username='testuser',
            password_hash=generate_password_hash('testpass')
        )
        db.session.add(user)
        db.session.commit()
        print("創建測試用戶: testuser")
    else:
        print("測試用戶已存在: testuser")
    
    # 創建測試客戶端
    client = app.test_client()
    
    # 測試登錄
    login_response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    print(f"登錄狀態碼: {login_response.status_code}")
    print(f"登錄響應: {login_response.get_data(as_text=True)}")
    
    # 測試認證後的 API 調用
    response = client.get('/api/agent/tip', headers={'X-Api-Key': 'test-key'})
    print(f"API 狀態碼: {response.status_code}")
    print(f"API 響應: {response.get_data(as_text=True)}")

# 清理
try:
    os.unlink(db_path)
except:
    pass
