#!/usr/bin/env python3
"""
PostgreSQL 連接測試 - 檢查生產環境數據庫狀態
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Sheep

def test_postgresql_connection():
    """測試 PostgreSQL 連接和基本功能"""
    try:
        app = create_app()
        
        with app.app_context():
            print("🔗 正在測試 PostgreSQL 連接...")
            
            # 測試資料庫連接
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT 1"))
                print("✅ PostgreSQL 連接成功")
            
            # 檢查現有用戶數量
            user_count = User.query.count()
            print(f"📊 現有用戶數量: {user_count}")
            
            # 檢查現有羊隻數量
            sheep_count = Sheep.query.count()
            print(f"🐐 現有羊隻數量: {sheep_count}")
            
            # 測試表結構
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 資料庫表數量: {len(tables)}")
            if tables:
                print(f"📋 表名稱: {', '.join(tables[:5])}...")
            
            # 測試 Flask 應用
            client = app.test_client()
            
            # 測試靜態路由
            response = client.get('/')
            print(f"🌐 主頁路由測試 - 狀態碼: {response.status_code}")
            
            # 測試 API 端點 (不需要登入的)
            response = client.get('/api/auth/status')
            print(f"🔐 認證狀態 API 測試 - 狀態碼: {response.status_code}")
            
            print("🎉 PostgreSQL 和應用程式基本功能正常！")
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        print("💡 請檢查:")
        print("   1. PostgreSQL 服務是否正在運行")
        print("   2. 資料庫連接參數是否正確")
        print("   3. 用戶權限是否足夠")

if __name__ == '__main__':
    test_postgresql_connection()
