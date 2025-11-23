from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, EventTypeOption, EventDescriptionOption
from app import db

bp = Blueprint('auth', __name__)

def create_default_event_options_for_user(user):
    """為新用戶創建一套預設的事件類型和描述選項"""
    default_options = {
        "疫苗接種": ["口蹄疫疫苗", "炭疽病疫苗", "破傷風類毒素"],
        "疾病治療": ["盤尼西林注射", "抗生素治療", "消炎藥"],
        "配種": ["自然配種", "人工授精"],
        "產仔": ["單胎", "雙胎", "三胎以上"],
        "體重記錄": [],
        "飼料調整": ["更換精料", "增加草料", "補充礦物質"],
        "驅蟲": ["內寄生蟲 (口服)", "外寄生蟲 (噴灑)"],
        "特殊觀察": ["食慾不振", "跛行", "精神沉鬱"],
    "AI營養與ESG建議": [],
        "其他": []
    }
    
    for type_name, descriptions in default_options.items():
        event_type = EventTypeOption(user_id=user.id, name=type_name, is_default=True)
        db.session.add(event_type)
        db.session.flush()
        
        for desc_text in descriptions:
            description = EventDescriptionOption(
                user_id=user.id,
                event_type_option_id=event_type.id,
                description=desc_text,
                is_default=True
            )
            db.session.add(description)

@bp.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify(error='您已登入'), 400

    data = request.get_json()
    if not data:
        return jsonify(error='請求中未包含 JSON 數據'), 400
        
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify(error='使用者名稱和密碼為必填項'), 400

    if User.query.filter_by(username=username).first():
        return jsonify(error='此使用者名稱已被註冊'), 409

    try:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        create_default_event_options_for_user(new_user)
        
        db.session.commit()
        
        login_user(new_user, remember=True)

        return jsonify(
            success=True, 
            message='註冊成功',
            user={'username': new_user.username}
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'註冊失敗: {str(e)}'), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        if current_user.is_authenticated:
            return jsonify(success=True, message='用戶已登入')

        data = request.get_json()
        if not data:
            return jsonify(error='請求中未包含 JSON 數據'), 400

        username = data.get('username')
        password = data.get('password')
        
        print(f"Login attempt for user: {username}")  # Debug log
        
        user = User.query.filter_by(username=username).first()
        print(f"User found: {user is not None}")  # Debug log
        
        if user:
            password_valid = user.check_password(password)
            print(f"Password valid: {password_valid}")  # Debug log
            
            if password_valid:
                login_user(user, remember=True)
                return jsonify(
                    success=True, 
                    message='登入成功',
                    user={'username': user.username}
                )
        
        return jsonify(error='無效的使用者名稱或密碼'), 401
        
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()
        return jsonify(error=f'登入時發生錯誤: {str(e)}'), 500

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify(success=True, message='登出成功')

@bp.route('/status', methods=['GET'])
def auth_status():
    if current_user.is_authenticated:
        return jsonify(logged_in=True, user={'username': current_user.username})
    else:
        return jsonify(logged_in=False)


@bp.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點，用於 Docker 容器監控"""
    try:
        # 檢查資料庫連線
        from app.models import User
        User.query.limit(1).first()
        
        return jsonify({
            'status': 'healthy',
            'message': '服務運行正常',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': '服務異常',
            'error': str(e)
        }), 503