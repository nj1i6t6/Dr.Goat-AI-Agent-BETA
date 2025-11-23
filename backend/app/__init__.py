import os
from flask import Flask, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv

try:  # pragma: no cover - optional dependency for real Redis
    from redis import Redis  # type: ignore
except ImportError:  # pragma: no cover
    Redis = None  # type: ignore

from .session_interface import RedisSessionInterface
from .in_memory_redis import InMemoryRedis
from .simple_queue import SimpleQueue
from .rag_loader import ensure_vectors

# 載入 .env 設定：優先採用 DOTENV_PATH，其次自動尋找專案根目錄的 .env
dotenv_path = os.environ.get('DOTENV_PATH') or find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path)
    try:
        print(f"Loaded .env: {dotenv_path}")
    except Exception:
        pass
else:
    # 若找不到檔案仍呼叫一次，允許從系統環境變數載入
    load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def _build_redis_url() -> str:
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        return redis_url

    host = os.environ.get('REDIS_HOST', 'localhost')
    port = os.environ.get('REDIS_PORT', '6379')
    db_index = os.environ.get('REDIS_DB', '0')
    password = os.environ.get('REDIS_PASSWORD')

    if password:
        return f"redis://:{password}@{host}:{port}/{db_index}"
    return f"redis://{host}:{port}/{db_index}"


def _init_redis_client(app: Flask):
    redis_url = _build_redis_url()
    use_fake = os.environ.get('USE_FAKE_REDIS_FOR_TESTS') == '1'
    client = None

    if not use_fake and Redis is not None:  # pragma: no branch - optional runtime dependency
        try:
            client = Redis.from_url(redis_url, decode_responses=True)  # type: ignore[attr-defined]
            client.ping()
        except Exception:
            client = None

    if client is None:
        client = InMemoryRedis()

    app.config.setdefault('REDIS_URL', redis_url)
    app.extensions['redis_client'] = client
    return client

def _load_api_hmac_secret() -> bytes:
    secret_value = os.environ.get('API_HMAC_SECRET')
    if not secret_value:
        raise RuntimeError('API_HMAC_SECRET 未設定，無法啟動應用程式')

    secret_bytes = secret_value.encode('utf-8')
    if len(secret_bytes) < 32:
        raise ValueError('API_HMAC_SECRET 長度不足，至少需要 32 bytes')
    return secret_bytes


def create_app():
    # --- 【修改一：配置靜態檔案路徑】 ---
    # 告訴 Flask，我們的靜態檔案（打包後的前端）在哪裡
    # '..' 代表上一層目錄 (backend -> project root)
    # 'frontend/dist' 是 Vite 打包後的輸出目錄
    app = Flask(__name__,
                static_folder=os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist'),
                static_url_path='/')

    # --- 配置 ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY')
    app.config['API_HMAC_SECRET'] = _load_api_hmac_secret()
    
    # --- 【檔案上傳大小限制】 ---
    # 設定最大檔案上傳大小為 50MB
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    
    # --- 【安全性改進：CORS 設定】 ---
    # 根據環境變數決定允許的來源
    cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
    if cors_origins == ['*']:
        # 開發環境：允許所有來源
        CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    else:
        # 生產環境：僅允許指定的來源
        CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

    # PostgreSQL 配置 - 使用正確的環境變數名稱
    db_user = os.environ.get('POSTGRES_USER')
    db_pass = os.environ.get('POSTGRES_PASSWORD')
    db_host = os.environ.get('POSTGRES_HOST', 'db')  # Docker Compose 服務名稱
    db_port = os.environ.get('POSTGRES_PORT', '5432')
    db_name = os.environ.get('POSTGRES_DB')
    
    # 檢查是否有資料庫配置，如果沒有則使用默認的 SQLite
    if all([db_user, db_pass, db_name]):
        db_uri = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        print(f"使用 PostgreSQL 資料庫: {db_host}:{db_port}/{db_name}")
    elif not app.config.get('SQLALCHEMY_DATABASE_URI'):
        # 如果沒有設定任何資料庫 URI，使用默認的 SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
        print("使用 SQLite 資料庫: app.db")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Redis / Session 設定 ---
    redis_client = _init_redis_client(app)
    app.config.setdefault('SESSION_TYPE', 'redis')
    app.config.setdefault('SESSION_USE_SIGNER', True)
    app.config.setdefault('SESSION_PERMANENT', False)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    app.config['SESSION_REDIS'] = redis_client
    app.session_interface = RedisSessionInterface(redis_client)

    queue_name = os.environ.get('RQ_QUEUE_NAME', 'default')
    app.config.setdefault('RQ_QUEUE_NAME', queue_name)
    app.extensions['rq_queue'] = SimpleQueue(queue_name, connection=redis_client)

    # --- 初始化擴展 ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify(error="Login required"), 401

    with app.app_context():
        # --- 自動資料庫初始化 ---
        try:
            # 檢查資料庫是否已初始化
            db.engine.execute('SELECT 1 FROM user LIMIT 1')
            print("資料庫已存在，跳過初始化")
        except Exception:
            print("資料庫未初始化，正在創建表格...")
            try:
                db.create_all()
                print("資料庫表格創建成功")
            except Exception as e:
                print(f"資料庫初始化失敗: {e}")
        
        # --- 註冊 API 藍圖 ---
        from .api import (
            auth as auth_bp,
            sheep as sheep_bp,
            data_management as data_management_bp,
            agent as agent_bp,
            dashboard as dashboard_bp,
            prediction as prediction_bp,
            traceability as traceability_bp,
            tasks as tasks_bp,
            iot as iot_bp,
            verify as verify_bp,
            finance as finance_bp,
            bi as bi_bp,
            activity as activity_bp,
        )
        app.register_blueprint(auth_bp.bp, url_prefix='/api/auth')
        app.register_blueprint(sheep_bp.bp, url_prefix='/api/sheep')
        app.register_blueprint(data_management_bp.bp, url_prefix='/api/data')
        app.register_blueprint(agent_bp.bp, url_prefix='/api/agent')
        app.register_blueprint(dashboard_bp.bp, url_prefix='/api/dashboard')
        app.register_blueprint(prediction_bp.bp, url_prefix='/api/prediction')
        app.register_blueprint(traceability_bp.bp, url_prefix='/api/traceability')
        app.register_blueprint(tasks_bp.bp, url_prefix='/api/tasks')
        app.register_blueprint(iot_bp.bp, url_prefix='/api/iot')
        app.register_blueprint(verify_bp.bp, url_prefix='/api/verify')
        app.register_blueprint(finance_bp.bp, url_prefix='/api/finance')
        app.register_blueprint(bi_bp.bp, url_prefix='/api/bi')
        app.register_blueprint(activity_bp.bp, url_prefix='/api/activity')

        # --- OpenAPI 規格與 Swagger UI ---
        @app.route('/openapi.yaml')
        def serve_openapi_yaml():
            # 從 backend 目錄提供 openapi.yaml
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            yaml_path = os.path.join(backend_dir, 'openapi.yaml')
            if os.path.exists(yaml_path):
                return send_from_directory(backend_dir, 'openapi.yaml')
            return jsonify(error='openapi.yaml not found'), 404

        @app.route('/docs')
        def swagger_ui():
            # 簡易 Swagger UI（使用 CDN）
            return (
                """
                <!DOCTYPE html>
                <html lang="zh-Hant">
                <head>
                    <meta charset="UTF-8" />
                    <title>Goat Nutrition API Docs</title>
                    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
                    <style>body{margin:0;}#swagger-ui{max-width: 100vw;}</style>
                </head>
                <body>
                    <div id="swagger-ui"></div>
                    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
                    <script>
                        window.onload = () => {
                            window.ui = SwaggerUIBundle({
                                url: '/openapi.yaml',
                                dom_id: '#swagger-ui',
                                presets: [SwaggerUIBundle.presets.apis],
                                layout: 'BaseLayout'
                            });
                        };
                    </script>
                </body>
                </html>
                """
            )

        # --- 【修改二：添加捕獲所有路由的規則】 ---
        # 這個規則確保，任何不匹配 API 的請求，都會返回前端的 index.html
        # 這是讓 Vue Router (History 模式) 正常工作的關鍵
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve(path):
            if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
                return send_from_directory(app.static_folder, path)
            else:
                return send_from_directory(app.static_folder, 'index.html')

        try:
            ensure_vectors()
        except Exception as exc:  # pragma: no cover - defensive logging
            app.logger.warning("RAG preload failed: %s", exc)

        return app
