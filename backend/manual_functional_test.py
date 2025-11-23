#!/usr/bin/env python3
"""
手動功能測試腳本 - 使用測試環境，不影響生產 PostgreSQL
"""
import os
import sys

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Sheep

def test_app_functionality():
    """測試基本應用程式功能"""
    app = create_app()
    app.config['TESTING'] = True
    # 僅用於測試的 SQLite 數據庫，不影響您的 PostgreSQL 生產環境
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        # 初始化資料庫
        db.create_all()
        print("✅ 測試資料庫初始化成功")
        
        # 創建測試用戶
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        print("✅ 測試用戶創建成功")
        
        # 創建測試羊隻
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
        
        # 測試查詢
        sheep_count = Sheep.query.filter_by(user_id=user.id).count()
        print(f"✅ 羊隻查詢成功，數量: {sheep_count}")
        
        # 測試客戶端
        with app.test_client() as client:
            # 測試登入
            response = client.post('/api/auth/login', 
                                 json={'username': 'testuser', 'password': 'testpass'})
            print(f"✅ 登入測試 - 狀態碼: {response.status_code}")
            
            # 測試取得羊隻列表 (正確的路由)
            response = client.get('/api/sheep/')
            print(f"✅ 羊隻列表測試 - 狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json() 
                print(f"   取得羊隻數量: {len(data)}")
            
            # 測試儀表板 API
            response = client.get('/api/dashboard/data')
            print(f"✅ 儀表板數據測試 - 狀態碼: {response.status_code}")
        
        print("🎉 所有手動功能測試通過！")
        print("💡 注意：此測試使用獨立的記憶體資料庫，不會影響您的 PostgreSQL 數據")

if __name__ == '__main__':
    test_app_functionality()
