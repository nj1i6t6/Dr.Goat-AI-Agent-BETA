#.\.venv\Scripts\Activate.ps1
#python generate_architecture.py
# generate_architecture.py
from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Nginx
from diagrams.programming.framework import Flask
# --- CHANGE 1: Import Javascript from language, not VueJS from framework ---
from diagrams.programming.language import Javascript 
from diagrams.onprem.container import Docker
from diagrams.onprem.vcs import Github
from diagrams.onprem.ci import GithubActions

# graph_attr 設定，可以調整字體等，避免圖片中的中文變亂碼
graph_attr = {
    "fontsize": "16",
    "fontname": "Microsoft YaHei" # 使用微軟雅黑體
}

print("腳本開始執行，準備生成圖表...")

with Diagram("領頭羊博士 - 部署架構圖", show=False, direction="TB", graph_attr=graph_attr):

    user = Github("開發者/使用者")

    with Cluster("雲端主機 (Cloud Host)"):
        with Cluster("Docker 環境"):
            
            with Cluster("前端服務 (Frontend)"):
                frontend_server = Nginx("Nginx")
                # --- CHANGE 2: Use Javascript class instead of VueJS ---
                vue_app = Javascript("Vue.js App") 
                frontend_server >> Edge(label="serve static files") >> vue_app

            with Cluster("後端服務 (Backend)"):
                backend_server = Flask("Flask App (API)")
                
            with Cluster("資料庫服務 (Database)"):
                db = PostgreSQL("PostgreSQL DB")

            backend_server >> Edge(label="讀寫資料") >> db
            frontend_server >> Edge(label="API 請求") >> backend_server
    
    with Cluster("CI/CD 流程"):
        actions = GithubActions("GitHub Actions")
        docker_registry = Docker("Docker Hub")

        user >> Edge(label="git push") >> actions
        actions >> Edge(label="build & push image") >> docker_registry
        actions >> Edge(label="deploy to host") >> frontend_server
        actions >> Edge(label="deploy to host") >> backend_server

print("圖表已成功生成！請查看專案資料夾下的 '領頭羊博士_-_部署架構圖.png'")