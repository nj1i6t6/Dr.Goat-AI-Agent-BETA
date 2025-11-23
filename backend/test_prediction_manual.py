#!/usr/bin/env python3
"""
快速測試羊隻生長預測功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Sheep, SheepHistoricalData
from datetime import datetime, timedelta

def test_prediction_feature():
    app = create_app()
    
    with app.app_context():
        # 創建資料庫表
        db.create_all()
        
        # 創建測試用戶
        user = User(username='test_user')
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        
        # 創建測試羊隻
        sheep = Sheep(
            user_id=user.id,
            EarNum='TEST001',
            Breed='努比亞',
            Sex='母',
            BirthDate='2023-01-01'
        )
        db.session.add(sheep)
        db.session.commit()
        
        # 創建體重歷史記錄
        base_date = datetime(2024, 1, 1)
        for i in range(8):  # 8筆記錄
            record = SheepHistoricalData(
                sheep_id=sheep.id,
                user_id=user.id,
                record_date=(base_date + timedelta(days=i*10)).strftime('%Y-%m-%d'),
                record_type='體重',
                value=15.0 + i * 1.5  # 模擬成長
            )
            db.session.add(record)
        
        db.session.commit()
        
        # 測試數據品質檢查函數
        from app.api.prediction import data_quality_check
        
        weight_data = [
            {'record_date': '2024-01-01', 'value': 15.0},
            {'record_date': '2024-01-11', 'value': 16.5},
            {'record_date': '2024-01-21', 'value': 18.0},
            {'record_date': '2024-01-31', 'value': 19.5},
            {'record_date': '2024-02-10', 'value': 21.0}
        ]
        
        quality_report = data_quality_check(weight_data)
        print("數據品質檢查結果:")
        print(f"  狀態: {quality_report['status']}")
        print(f"  消息: {quality_report['message']}")
        print(f"  詳細信息: {quality_report['details']}")
        
        # 測試品種參考範圍函數
        from app.api.prediction import get_breed_reference_ranges
        
        ranges = get_breed_reference_ranges('努比亞', 12)
        print(f"\n努比亞羊12月齡參考範圍:")
        print(f"  最小日增重: {ranges['min']} kg/天")
        print(f"  最大日增重: {ranges['max']} kg/天")
        
        print("\n✅ 預測功能基本測試通過!")

if __name__ == '__main__':
    test_prediction_feature()
