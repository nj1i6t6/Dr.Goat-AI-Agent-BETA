import os
from app import create_app, db
from app.models import User, Sheep, SheepEvent, ChatHistory

# 從工廠函數創建 app 實例
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """為 flask shell 命令提供上下文，方便調試。"""
    return {
        'db': db,
        'User': User,
        'Sheep': Sheep,
        'SheepEvent': SheepEvent,
        'ChatHistory': ChatHistory
    }

if __name__ == '__main__':
    # 檢測是否在 Codespaces 環境中，如果是則自動創建資料庫表格
    is_codespaces = os.environ.get('CODESPACES') or os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')
    
    # 在應用程式上下文中執行操作，確保擴展等能正確初始化
    with app.app_context():
        # 如果在 Codespaces 環境且使用 SQLite，自動創建表格
        if is_codespaces and 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            print("檢測到 Codespaces 環境，使用 SQLite 並自動創建表格...")
            db.create_all()
            print("資料庫表格創建完成！")
        # 這裡可以放置需要在啟動時執行的命令，例如 db.create_all() (但在使用 migrate 後不建議)
    
    # 從環境變數讀取配置
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')  # 改為 0.0.0.0 以支援外網訪問
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']  # 生產環境預設關閉 debug

    print("===================================================")
    print(f" * Backend server starting on http://{host}:{port}")
    print(f" * Debug mode: {'on' if debug else 'off'}")
    print("===================================================")
    
    # 使用 app.run 啟動開發伺服器
    # 在生產環境中，應使用 Gunicorn 或 Waitress
    app.run(host=host, port=port, debug=debug)