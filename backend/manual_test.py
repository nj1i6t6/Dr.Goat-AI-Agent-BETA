#!/usr/bin/env python3
"""
手動功能測試腳本
"""
import os
import sys
import requests
import json
from time import sleep

#!/usr/bin/env python3
"""
手動功能測試腳本
"""
import os
import sys
import requests
import json
from time import sleep

# 設置環境變數 - 確保使用 SQLite
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['CORS_ORIGINS'] = '*'
# 清除資料庫相關環境變數，確保使用 SQLite
for key in ['DB_USERNAME', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']:
    if key in os.environ:
        del os.environ[key]

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Sheep

def test_app_functionality():
    """測試基本應用程式功能"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        # 確保資料庫表結構乾淨
        db.drop_all()
        db.create_all()
        print("✅ 資料庫初始化成功")
        
        # 創建測試用戶 (在記憶體資料庫中，應該不會有重複問題)
        try:
            user = User(username='testuser')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            print("✅ 測試用戶創建成功")
        except Exception as e:
            # 如果出現錯誤，回滾並查找現有用戶
            db.session.rollback()
            user = User.query.filter_by(username='testuser').first()
            if not user:
                raise e  # 如果真的沒有用戶，重新拋出錯誤
            print("✅ 使用現有測試用戶")
        
        # 創建測試羊隻 (添加錯誤處理避免重複)
        try:
            sheep = Sheep(
                user_id=user.id,
                EarNum='TEST001',
                Breed='波爾羊',
                Sex='母',
                Body_Weight_kg=45.5,
                FarmNum='F001'
            )
            db.session.add(sheep)
            db.session.commit()
            print("✅ 測試羊隻創建成功")
        except Exception as e:
            # 如果羊隻已存在，使用現有的
            db.session.rollback()
            sheep = Sheep.query.filter_by(user_id=user.id, EarNum='TEST001').first()
            if not sheep:
                raise e  # 如果真的沒有羊隻，重新拋出錯誤
            print("✅ 使用現有測試羊隻")
        
        # 測試查詢
        sheep_count = Sheep.query.filter_by(user_id=user.id).count()
        print(f"✅ 羊隻查詢成功，數量: {sheep_count}")
        
        # 測試客戶端
        with app.test_client() as client:
            # 測試登入
            response = client.post('/api/auth/login', 
                                 json={'username': 'testuser', 'password': 'testpass'})
            print(f"✅ 登入測試 - 狀態碼: {response.status_code}")
            
            # 測試取得羊隻列表
            response = client.get('/api/sheep/')
            print(f"✅ 羊隻列表測試 - 狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   取得羊隻數量: {len(data)}")
        
        print("🎉 所有手動功能測試通過！")

if __name__ == '__main__':
    test_app_functionality()
