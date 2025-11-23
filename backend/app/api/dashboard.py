from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models import db, Sheep, SheepEvent, SheepHistoricalData, EventTypeOption, EventDescriptionOption
from sqlalchemy import func, case
from sqlalchemy.orm import aliased
from datetime import datetime, date, timedelta
import numpy as np
from app.cache import get_dashboard_cache, set_dashboard_cache, clear_dashboard_cache, get_user_lock

bp = Blueprint('dashboard', __name__)


@bp.route('/data', methods=['GET'])
@login_required
def get_dashboard_data():
    """獲取儀表板所需的聚合數據"""
    try:
        user_id = current_user.id
        today = date.today()
        seven_days_later = today + timedelta(days=7)
        # 先嘗試命中快取
        cached = get_dashboard_cache(user_id)
        if cached:
            return jsonify(cached)
        
        # 避免併發重算，對單一 user_id 加鎖
        lock = get_user_lock(user_id)
        with lock:
            # 雙重檢查
            cached2 = get_dashboard_cache(user_id)
            if cached2:
                return jsonify(cached2)

        # 1. 常規提醒事項
        reminders = []
        reminder_fields = {
            "next_vaccination_due_date": "疫苗接種",
            "next_deworming_due_date": "驅蟲",
            "expected_lambing_date": "預產期"
        }
        
        # 查詢所有有設定提醒日期的羊隻
        reminder_sheep = db.session.query(
            Sheep.EarNum,
            Sheep.next_vaccination_due_date,
            Sheep.next_deworming_due_date,
            Sheep.expected_lambing_date
        ).filter(
            Sheep.user_id == user_id,
            (Sheep.next_vaccination_due_date != None) |
            (Sheep.next_deworming_due_date != None) |
            (Sheep.expected_lambing_date != None)
        ).all()

        for s in reminder_sheep:
            for field, type_name in reminder_fields.items():
                due_date_str = getattr(s, field)
                if due_date_str:
                    due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    if due_date_obj <= seven_days_later:
                        status = "即將到期"
                        if due_date_obj < today: status = "已過期"
                        reminders.append({"ear_num": s.EarNum, "type": type_name, "due_date": due_date_str, "status": status})

        # 2. 停藥期提醒
        medication_events = db.session.query(
            Sheep.EarNum, SheepEvent.event_date, SheepEvent.medication, SheepEvent.withdrawal_days
        ).join(Sheep, Sheep.id == SheepEvent.sheep_id)\
         .filter(
             Sheep.user_id == user_id,
             SheepEvent.withdrawal_days != None,
             SheepEvent.withdrawal_days > 0
         ).all()

        for event in medication_events:
            event_date_obj = datetime.strptime(event.event_date, '%Y-%m-%d').date()
            end_date = event_date_obj + timedelta(days=event.withdrawal_days)
            if end_date >= today:
                reminders.append({
                    "ear_num": event.EarNum,
                    "type": f"停藥期 ({event.medication or '未指定藥品'})",
                    "due_date": end_date.strftime('%Y-%m-%d'),
                    "status": "停藥中"
                })

        # 3. 羊群狀態摘要
        flock_status_summary = db.session.query(
            Sheep.status, func.count(Sheep.id)
        ).filter(Sheep.user_id == user_id, Sheep.status != None, Sheep.status != '').group_by(Sheep.status).all()
        flock_summary_list = [{"status": status, "count": count} for status, count in flock_status_summary]

        # 4. 健康與福利警示（批次查詢 + SQL 限窗）
        health_alerts = []

        all_sheep = Sheep.query.with_entities(
            Sheep.id, Sheep.EarNum, Sheep.BirthDate, Sheep.Breed
        ).filter_by(user_id=user_id).all()
        sheep_by_id = {s.id: s for s in all_sheep}

        # 需要的時間窗：體重 30 天、奶量 14 天
        cutoff_weight = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        cutoff_milk = (today - timedelta(days=14)).strftime('%Y-%m-%d')

        # 批次抓近 30 天內的體重與近 14 天內的奶量記錄
        recent_hist = db.session.query(
            SheepHistoricalData.sheep_id,
            SheepHistoricalData.record_type,
            SheepHistoricalData.record_date,
            SheepHistoricalData.value
        ).filter(
            SheepHistoricalData.user_id == user_id,
            (
                (
                    SheepHistoricalData.record_type == 'Body_Weight_kg'
                ) & (SheepHistoricalData.record_date >= cutoff_weight)
            ) | (
                (
                    SheepHistoricalData.record_type == 'milk_yield_kg_day'
                ) & (SheepHistoricalData.record_date >= cutoff_milk)
            )
        ).order_by(
            SheepHistoricalData.sheep_id.asc(),
            SheepHistoricalData.record_type.asc(),
            SheepHistoricalData.record_date.asc()
        ).all()

        weight_map = {}
        milk_map = {}
        for sid, rtype, rdate, val in recent_hist:
            try:
                d = datetime.strptime(rdate, '%Y-%m-%d').date()
            except Exception:
                continue
            if rtype == 'Body_Weight_kg':
                weight_map.setdefault(sid, []).append((d, float(val)))
            elif rtype == 'milk_yield_kg_day':
                milk_map.setdefault(sid, []).append((d, float(val)))

        # 輔助方法：計算線性回歸斜率（天 vs 值），缺資料返回 None
        def linear_slope(date_value_pairs):
            if len(date_value_pairs) < 3:
                return None
            base = min(d for d, _ in date_value_pairs)
            x = np.array([(d - base).days for d, _ in date_value_pairs], dtype=float).reshape(-1, 1)
            y = np.array([v for _, v in date_value_pairs], dtype=float)
            if len(np.unique(x)) < 2:
                return None
            # 簡易最小平方法（不引入 sklearn 以避免額外依賴/啟動成本）
            # slope = cov(x,y)/var(x)
            x1 = x.flatten()
            x_mean = np.mean(x1)
            y_mean = np.mean(y)
            denom = np.sum((x1 - x_mean) ** 2)
            if denom == 0:
                return None
            slope = np.sum((x1 - x_mean) * (y - y_mean)) / denom
            return float(slope)

        # 輔助方法：品種/月齡參考範圍（與 prediction.py 保持一致的邏輯簡化版）
        def breed_gain_ref(breed, age_months):
            ranges = {
                '努比亞': {'min': 0.08, 'max': 0.15},
                '阿爾拜因': {'min': 0.07, 'max': 0.13},
                '撒能': {'min': 0.09, 'max': 0.16},
                '波爾': {'min': 0.10, 'max': 0.18},
                '台灣黑山羊': {'min': 0.06, 'max': 0.12},
                'default': {'min': 0.07, 'max': 0.14}
            }
            if age_months is not None and age_months < 6:
                mul = 1.3
            elif age_months is not None and age_months < 12:
                mul = 1.1
            else:
                mul = 1.0
            base = ranges.get(breed, ranges['default'])
            return {'min': round(base['min'] * mul, 3), 'max': round(base['max'] * mul, 3)}

        # 掃描當前使用者所有羊隻，生成健康警示
        for s in all_sheep:
            # 體重下降（近14天 vs 前14天平均體重下降 > 5%）
            hist_30 = weight_map.get(s.id, [])
            if len(hist_30) >= 4:
                # 分段：最近14天、之前的14天
                cut_14 = today - timedelta(days=14)
                prev_segment = [v for d, v in hist_30 if d < cut_14]
                recent_segment = [v for d, v in hist_30 if d >= cut_14]
                if len(prev_segment) >= 2 and len(recent_segment) >= 2:
                    prev_avg = float(np.mean(prev_segment))
                    recent_avg = float(np.mean(recent_segment))
                    if prev_avg > 0 and (prev_avg - recent_avg) / prev_avg > 0.05:
                        health_alerts.append({
                            'ear_num': s.EarNum,
                            'type': '體重下降',
                            'message': f'近14天平均體重較前期下降 {(prev_avg - recent_avg):.2f} kg（>{5}%）',
                            'severity': 'danger'
                        })

            # 生長偏慢（近30天體重線性斜率 < 品種/月齡下限）
            if len(hist_30) >= 3:
                # 估月齡
                age_months = None
                try:
                    if s.BirthDate:
                        b = datetime.strptime(s.BirthDate, '%Y-%m-%d').date()
                        age_months = (today.year - b.year) * 12 + (today.month - b.month)
                except Exception:
                    pass
                ref = breed_gain_ref(s.Breed, age_months)
                slope = linear_slope(hist_30)  # kg/天
                if slope is not None and slope < ref['min']:
                    health_alerts.append({
                        'ear_num': s.EarNum,
                        'type': '生長偏慢',
                        'message': f'近30天平均日增重 {slope:.3f} kg/天 低於參考下限 {ref["min"]} kg/天',
                        'severity': 'warning'
                    })

            # 奶量變化（近7天平均 vs 前7天平均 下降 > 25%）
            milk_14 = milk_map.get(s.id, [])
            if len(milk_14) >= 4:
                cut_7 = today - timedelta(days=7)
                prev_m = [v for d, v in milk_14 if d < cut_7]
                recent_m = [v for d, v in milk_14 if d >= cut_7]
                if len(prev_m) >= 2 and len(recent_m) >= 2:
                    pavg = float(np.mean(prev_m))
                    ravg = float(np.mean(recent_m))
                    if pavg > 0 and (pavg - ravg) / pavg > 0.25:
                        health_alerts.append({
                            'ear_num': s.EarNum,
                            'type': '奶量變化',
                            'message': f'近7天平均奶量較前期下降 {(pavg - ravg):.2f} kg/天（>{25}%）',
                            'severity': 'warning'
                        })
        
        # 5. ESG 指標模擬
        fcr_value = 4.5 # 簡化模擬值

        payload = {
            "reminders": sorted(reminders, key=lambda x: (x.get("due_date", "9999-99-99"))),
            "health_alerts": health_alerts,
            "flock_status_summary": flock_summary_list,
            "esg_metrics": {"fcr": fcr_value}
        }

        # 寫入快取
        set_dashboard_cache(user_id, payload)
        return jsonify(payload)
        
    except Exception as e:
        current_app.logger.error(f"獲取儀表板數據時發生錯誤: {e}", exc_info=True)
        return jsonify(error=f"伺服器內部錯誤，無法生成儀表板數據: {str(e)}"), 500

@bp.route('/farm_report', methods=['GET'])
@login_required
def get_farm_report():
    """生成牧場報告"""
    try:
        user_id = current_user.id
        
        flock_composition = {
            'by_breed': db.session.query(Sheep.Breed, func.count(Sheep.id)).filter(Sheep.user_id == user_id, Sheep.Breed != None).group_by(Sheep.Breed).all(),
            'by_sex': db.session.query(Sheep.Sex, func.count(Sheep.id)).filter(Sheep.user_id == user_id, Sheep.Sex != None).group_by(Sheep.Sex).all()
        }
        
        production_summary = {
            'avg_birth_weight': db.session.query(func.avg(Sheep.BirWei)).filter(Sheep.user_id == user_id, Sheep.BirWei != None).scalar(),
            'avg_litter_size': db.session.query(func.avg(Sheep.LittleSize)).filter(Sheep.user_id == user_id, Sheep.LittleSize != None).scalar(),
            'avg_milk_yield': db.session.query(func.avg(SheepHistoricalData.value)).filter(SheepHistoricalData.user_id == user_id, SheepHistoricalData.record_type == 'milk_yield_kg_day').scalar()
        }
        
        disease_stats = db.session.query(
            SheepEvent.description, func.count(SheepEvent.id)
        ).filter(SheepEvent.user_id == user_id, SheepEvent.event_type == '疾病治療', SheepEvent.description != None)\
         .group_by(SheepEvent.description).order_by(func.count(SheepEvent.id).desc()).limit(5).all()

        report = {
            "flock_composition": {
                "by_breed": [{"name": item[0] or "未分類", "count": item[1]} for item in flock_composition['by_breed']],
                "by_sex": [{"name": item[0] or "未分類", "count": item[1]} for item in flock_composition['by_sex']],
                "total": db.session.query(func.count(Sheep.id)).filter(Sheep.user_id == user_id).scalar() or 0
            },
            "production_summary": {
                "avg_birth_weight": round(p, 2) if (p := production_summary['avg_birth_weight']) else None,
                "avg_litter_size": round(p, 1) if (p := production_summary['avg_litter_size']) else None,
                "avg_milk_yield": round(p, 2) if (p := production_summary['avg_milk_yield']) else None,
            },
            "health_summary": {
                "top_diseases": [{"name": item[0] or "未指定描述", "count": item[1]} for item in disease_stats]
            }
        }
        
        return jsonify(report)

    except Exception as e:
        current_app.logger.error(f"生成牧場報告時發生錯誤: {e}", exc_info=True)
        return jsonify(error=f"伺服器內部錯誤，無法生成報告: {str(e)}"), 500

# --- 事件選項自訂 API ---

@bp.route('/event_options', methods=['GET'])
@login_required
def get_event_options():
    """取得用戶所有自訂與預設的事件選項"""
    types = EventTypeOption.query.filter_by(user_id=current_user.id).order_by(EventTypeOption.is_default.desc(), EventTypeOption.name).all()
    # 使用 to_dict 方法來序列化，它會自動處理關聯的 descriptions
    return jsonify([t.to_dict() for t in types])

@bp.route('/event_types', methods=['POST'])
@login_required
def add_event_type():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify(error="類型名稱為必填"), 400
    if EventTypeOption.query.filter_by(user_id=current_user.id, name=name).first():
        return jsonify(error=f"類型 '{name}' 已存在"), 409
    try:
        new_type = EventTypeOption(user_id=current_user.id, name=name, is_default=False)
        db.session.add(new_type)
        db.session.commit()
        return jsonify(new_type.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"新增失敗: {str(e)}"), 500

@bp.route('/event_types/<int:type_id>', methods=['DELETE'])
@login_required
def delete_event_type(type_id):
    option = EventTypeOption.query.get_or_404(type_id)
    if option.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    if option.is_default:
        return jsonify(error="不能刪除預設的事件類型"), 400
    try:
        db.session.delete(option)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"刪除失敗: {str(e)}"), 500

@bp.route('/event_descriptions', methods=['POST'])
@login_required
def add_event_description():
    data = request.get_json()
    type_id = data.get('event_type_option_id')
    description_text = data.get('description')
    if not all([type_id, description_text]):
        return jsonify(error="缺少必要參數"), 400
    
    parent_type = EventTypeOption.query.get_or_404(type_id)
    if parent_type.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    if EventDescriptionOption.query.filter_by(event_type_option_id=type_id, description=description_text).first():
        return jsonify(error=f"描述 '{description_text}' 已存在於此類型中"), 409
        
    try:
        new_desc = EventDescriptionOption(
            user_id=current_user.id,
            event_type_option_id=type_id,
            description=description_text,
            is_default=False
        )
        db.session.add(new_desc)
        db.session.commit()
        return jsonify(new_desc.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"新增失敗: {str(e)}"), 500

@bp.route('/event_descriptions/<int:desc_id>', methods=['DELETE'])
@login_required
def delete_event_description(desc_id):
    option = EventDescriptionOption.query.get_or_404(desc_id)
    if option.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    if option.is_default:
        return jsonify(error="不能刪除預設的簡要描述"), 400
    try:
        db.session.delete(option)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"刪除失敗: {str(e)}"), 500