#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/workspaces/Goat_Nutrition_App_Optimization_Test/backend')

# 設定環境變數
os.environ['POSTGRES_DB'] = ''
os.environ['POSTGRES_USER'] = ''
os.environ['POSTGRES_PASSWORD'] = ''
os.environ['POSTGRES_HOST'] = ''
os.environ['POSTGRES_PORT'] = ''

from app import create_app, db
from app.models import Sheep, SheepHistoricalData, User
from datetime import datetime

app = create_app()
with app.app_context():
    # 查找用戶
    user = User.query.filter_by(username='111111').first()
    if not user:
        print('❌ 用戶 111111 不存在')
        sys.exit(1)
    
    print(f'✅ 找到用戶: {user.username} (ID: {user.id})')
    
    # 查找或創建羊隻
    sheep = Sheep.query.filter_by(user_id=user.id, EarNum='0009AL166056').first()
    if not sheep:
        print('🐐 創建測試羊隻...')
        sheep = Sheep(
            user_id=user.id,
            EarNum='0009AL166056',
            Breed='努比亞',
            Sex='母',
            BirthDate='2023-01-01',
            Body_Weight_kg=25.0
        )
        db.session.add(sheep)
        db.session.commit()
        print(f'✅ 已創建羊隻: {sheep.EarNum} (ID: {sheep.id})')
    else:
        print(f'✅ 找到羊隻: {sheep.EarNum} (ID: {sheep.id})')
    
    # 檢查體重記錄
    records = SheepHistoricalData.query.filter_by(sheep_id=sheep.id, record_type='Body_Weight_kg').all()
    print(f'📊 體重記錄數量: {len(records)}')
    
    if len(records) < 3:
        print('📈 創建測試體重記錄...')
        # 創建一些測試數據
        test_records = [
            ('2024-06-01', 30.5),
            ('2024-06-15', 32.2),
            ('2024-07-01', 34.8),
            ('2024-07-15', 36.1),
            ('2024-08-01', 38.5)
        ]
        
        for date_str, weight in test_records:
            existing = SheepHistoricalData.query.filter_by(
                sheep_id=sheep.id,
                record_date=date_str,
                record_type='Body_Weight_kg'
            ).first()
            if not existing:
                record = SheepHistoricalData(
                    user_id=user.id,
                    sheep_id=sheep.id,
                    record_date=date_str,
                    record_type='Body_Weight_kg',
                    value=weight
                )
                db.session.add(record)
        
        db.session.commit()
        print('✅ 已創建測試體重記錄')
    
    # 再次檢查
    records = SheepHistoricalData.query.filter_by(sheep_id=sheep.id, record_type='Body_Weight_kg').all()
    print(f'📊 最終體重記錄數量: {len(records)}')
    for r in records:
        print(f'   📅 {r.record_date}: {r.value} kg')
    
    print('🎉 測試數據準備完成！現在可以測試預測功能了。')
