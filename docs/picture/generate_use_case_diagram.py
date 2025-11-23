from pathlib import Path


def generate_use_case_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"900\" height=\"600\" viewBox=\"0 0 900 600\">
<style>
  text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; font-size: 18px; fill: #1b1b1b; }
  .actor { stroke: #1b5e20; fill: #c8e6c9; stroke-width: 2; }
  .usecase { stroke: #0d47a1; fill: #e3f2fd; stroke-width: 2; }
  .connector { stroke: #424242; stroke-width: 2; fill: none; }
</style>
<rect width=\"100%\" height=\"100%\" fill=\"#fafafa\" />
<text x=\"450\" y=\"40\" text-anchor=\"middle\" font-size=\"28\" font-weight=\"bold\">使用案例圖 - Goat Nutrition</text>

<!-- Actors -->
<g>
  <ellipse class=\"actor\" cx=\"130\" cy=\"140\" rx=\"70\" ry=\"40\" />
  <text x=\"130\" y=\"145\" text-anchor=\"middle\">使用者</text>
</g>
<g>
  <ellipse class=\"actor\" cx=\"770\" cy=\"140\" rx=\"70\" ry=\"40\" />
  <text x=\"770\" y=\"145\" text-anchor=\"middle\">IoT裝置</text>
</g>

<!-- Use cases -->
<g>
  <ellipse class=\"usecase\" cx=\"450\" cy=\"150\" rx=\"140\" ry=\"45\" />
  <text x=\"450\" y=\"155\" text-anchor=\"middle\">羊群管理</text>
</g>
<g>
  <ellipse class=\"usecase\" cx=\"450\" cy=\"260\" rx=\"140\" ry=\"45\" />
  <text x=\"450\" y=\"265\" text-anchor=\"middle\">AI協作</text>
</g>
<g>
  <ellipse class=\"usecase\" cx=\"450\" cy=\"370\" rx=\"140\" ry=\"45\" />
  <text x=\"450\" y=\"375\" text-anchor=\"middle\">資料治理</text>
</g>
<g>
  <ellipse class=\"usecase\" cx=\"450\" cy=\"480\" rx=\"140\" ry=\"45\" />
  <text x=\"450\" y=\"485\" text-anchor=\"middle\">IoT自動化</text>
</g>
<g>
  <ellipse class=\"usecase\" cx=\"230\" cy=\"370\" rx=\"140\" ry=\"45\" />
  <text x=\"230\" y=\"375\" text-anchor=\"middle\">產銷履歷管理</text>
</g>

<!-- Connectors -->
<path class=\"connector\" d=\"M200 140 L320 150\" />
<path class=\"connector\" d=\"M200 160 L320 260\" />
<path class=\"connector\" d=\"M190 200 L320 370\" />
<path class=\"connector\" d=\"M170 210 L230 325\" />
<path class=\"connector\" d=\"M540 150 L700 150\" />
<path class=\"connector\" d=\"M540 260 L740 180\" />
<path class=\"connector\" d=\"M540 480 L730 190\" />
<path class=\"connector\" d=\"M340 430 L340 480 L310 480\" stroke-dasharray=\"6 6\" />
<text x=\"360\" y=\"460\" fill=\"#5d4037\">資料同步</text>

<!-- System boundary -->
<rect x=\"320\" y=\"90\" width=\"300\" height=\"420\" rx=\"18\" ry=\"18\" fill=\"none\" stroke=\"#9e9e9e\" stroke-dasharray=\"10 6\" stroke-width=\"2\" />
<text x=\"470\" y=\"110\" text-anchor=\"middle\" font-size=\"20\">Goat Nutrition 平台</text>
</svg>"""

    output_path = output_dir / "use_case_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path


def generate_deployment_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1100\" height=\"650\" viewBox=\"0 0 1100 650\">
<style>
  text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }
  .title { font-size: 30px; font-weight: bold; }
  .label { font-size: 18px; }
  .box { fill: #ffffff; stroke-width: 2.5; rx: 16; ry: 16; }
  .tier { fill: #f5f5f5; stroke: #bdbdbd; stroke-dasharray: 12 8; stroke-width: 2; }
  .arrow { stroke: #424242; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }
  .accent { font-size: 16px; fill: #424242; }
</style>
<defs>
  <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">
    <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#424242\" />
  </marker>
</defs>
<rect width=\"100%\" height=\"100%\" fill=\"#fafafa\" />
<text x=\"550\" y=\"50\" text-anchor=\"middle\" class=\"title\">部署架構示意圖 - Goat Nutrition</text>

<!-- Tiers -->
<rect class=\"tier\" x=\"70\" y=\"100\" width=\"260\" height=\"480\" />
<text x=\"200\" y=\"135\" text-anchor=\"middle\" class=\"accent\">Client / External</text>

<rect class=\"tier\" x=\"360\" y=\"100\" width=\"300\" height=\"480\" />
<text x=\"510\" y=\"135\" text-anchor=\"middle\" class=\"accent\">Application 層</text>

<rect class=\"tier\" x=\"690\" y=\"100\" width=\"340\" height=\"480\" />
<text x=\"860\" y=\"135\" text-anchor=\"middle\" class=\"accent\">資料與工作層</text>

<!-- Client -->
<rect class=\"box\" x=\"110\" y=\"180\" width=\"200\" height=\"120\" stroke=\"#039be5\" />
<text x=\"210\" y=\"230\" text-anchor=\"middle\" class=\"label\">Client</text>
<text x=\"210\" y=\"260\" text-anchor=\"middle\" class=\"accent\">瀏覽器 / 行動裝置</text>

<!-- External Gemini -->
<rect class=\"box\" x=\"110\" y=\"360\" width=\"200\" height=\"120\" stroke=\"#8e24aa\" />
<text x=\"210\" y=\"410\" text-anchor=\"middle\" class=\"label\">Gemini API</text>
<text x=\"210\" y=\"440\" text-anchor=\"middle\" class=\"accent\">LLM 推論服務</text>

<!-- Frontend -->
<rect class=\"box\" x=\"400\" y=\"200\" width=\"220\" height=\"100\" stroke=\"#fb8c00\" />
<text x=\"510\" y=\"240\" text-anchor=\"middle\" class=\"label\">Frontend</text>
<text x=\"510\" y=\"265\" text-anchor=\"middle\" class=\"accent\">Nginx / Vite 產出</text>

<!-- Backend -->
<rect class=\"box\" x=\"400\" y=\"360\" width=\"220\" height=\"120\" stroke=\"#43a047\" />
<text x=\"510\" y=\"410\" text-anchor=\"middle\" class=\"label\">Backend</text>
<text x=\"510\" y=\"440\" text-anchor=\"middle\" class=\"accent\">Flask API</text>

<!-- Worker -->
<rect class=\"box\" x=\"740\" y=\"200\" width=\"240\" height=\"110\" stroke=\"#d32f2f\" />
<text x=\"860\" y=\"245\" text-anchor=\"middle\" class=\"label\">Worker</text>
<text x=\"860\" y=\"275\" text-anchor=\"middle\" class=\"accent\">RQ / 背景任務</text>

<!-- Database -->
<rect class=\"box\" x=\"740\" y=\"360\" width=\"130\" height=\"130\" stroke=\"#3949ab\" />
<text x=\"805\" y=\"415\" text-anchor=\"middle\" class=\"label\">PostgreSQL</text>
<text x=\"805\" y=\"445\" text-anchor=\"middle\" class=\"accent\">交易資料</text>

<!-- Redis -->
<rect class=\"box\" x=\"900\" y=\"360\" width=\"130\" height=\"130\" stroke=\"#c62828\" />
<text x=\"965\" y=\"415\" text-anchor=\"middle\" class=\"label\">Redis</text>
<text x=\"965\" y=\"445\" text-anchor=\"middle\" class=\"accent\">快取 / 佇列</text>

<!-- Arrows -->
<path class=\"arrow\" d=\"M310 240 L400 240\" />
<path class=\"arrow\" d=\"M510 300 L510 360\" />
<path class=\"arrow\" d=\"M620 420 L740 420\" />
<path class=\"arrow\" d=\"M870 420 L900 420\" />
<path class=\"arrow\" d=\"M510 360 L740 255\" />
<path class=\"arrow\" d=\"M510 420 L870 255\" />
<path class=\"arrow\" d=\"M310 420 L400 420\" />
<path class=\"arrow\" d=\"M870 470 L870 545 L210 545 L210 480\" />

<text x=\"610\" y=\"230\" class=\"accent\">提供靜態資源</text>
<text x=\"610\" y=\"345\" class=\"accent\">API 請求</text>
<text x=\"700\" y=\"390\" class=\"accent\">資料持久化</text>
<text x=\"950\" y=\"470\" class=\"accent\">排程任務/快取</text>
<text x=\"630\" y=\"500\" class=\"accent\">LLM 輸入/輸出</text>

</svg>"""

    output_path = output_dir / "deployment_architecture.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path

def generate_backend_class_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1250\" height=\"750\" viewBox=\"0 0 1250 750\">
<style>
  text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }
  .title { font-size: 30px; font-weight: bold; }
  .module { fill: #ffffff; stroke-width: 2.7; rx: 18; ry: 18; }
  .api { stroke: #1565c0; }
  .core { stroke: #2e7d32; }
  .support { stroke: #6a1b9a; }
  .worker { stroke: #d84315; }
  .queue { fill: #fff3e0; stroke: #fb8c00; stroke-width: 2.5; }
  .label { font-size: 20px; font-weight: 600; }
  .path { font-size: 16px; fill: #424242; }
  .note { font-size: 15px; fill: #616161; }
  .accent { font-size: 15px; fill: #455a64; font-style: italic; }
  .arrow { stroke: #455a64; stroke-width: 2.5; fill: none; marker-end: url(#arrowhead); }
</style>
<defs>
  <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">
    <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#455a64\" />
  </marker>
</defs>
<rect width=\"100%\" height=\"100%\" fill=\"#f9fbff\" />
<text x=\"625\" y=\"55\" text-anchor=\"middle\" class=\"title\">後端模組關係圖 - Goat Nutrition</text>

<!-- API Blueprints -->
<rect class=\"module api\" x=\"90\" y=\"160\" width=\"230\" height=\"120\" />
<text text-anchor=\"middle\">
  <tspan x=\"205\" y=\"210\" class=\"label\">Sheep API</tspan>
  <tspan x=\"205\" y=\"236\" class=\"path\">app/api/sheep.py</tspan>
  <tspan x=\"205\" y=\"262\" class=\"note\">羊群 CRUD 與事件管理</tspan>
</text>

<rect class=\"module api\" x=\"480\" y=\"150\" width=\"250\" height=\"130\" />
<text text-anchor=\"middle\">
  <tspan x=\"605\" y=\"200\" class=\"label\">Agent API</tspan>
  <tspan x=\"605\" y=\"226\" class=\"path\">app/api/agent.py</tspan>
  <tspan x=\"605\" y=\"252\" class=\"note\">AI 提示增強與回覆生成</tspan>
</text>

<rect class=\"module api\" x=\"890\" y=\"160\" width=\"230\" height=\"120\" />
<text text-anchor=\"middle\">
  <tspan x=\"1005\" y=\"210\" class=\"label\">IoT API</tspan>
  <tspan x=\"1005\" y=\"236\" class=\"path\">app/api/iot.py</tspan>
  <tspan x=\"1005\" y=\"262\" class=\"note\">裝置註冊、資料上報與任務入列</tspan>
</text>

<!-- Core Models -->
<rect class=\"module core\" x=\"470\" y=\"340\" width=\"280\" height=\"140\" />
<text text-anchor=\"middle\">
  <tspan x=\"610\" y=\"390\" class=\"label\">Models</tspan>
  <tspan x=\"610\" y=\"416\" class=\"path\">app/models.py</tspan>
  <tspan x=\"610\" y=\"442\" class=\"note\">SQLAlchemy ORM 與資料表定義</tspan>
</text>

<!-- Support Modules -->
<rect class=\"module support\" x=\"90\" y=\"520\" width=\"260\" height=\"130\" />
<text text-anchor=\"middle\">
  <tspan x=\"220\" y=\"570\" class=\"label\">RAG Ingest</tspan>
  <tspan x=\"220\" y=\"596\" class=\"path\">scripts/ingest_docs.py</tspan>
  <tspan x=\"220\" y=\"622\" class=\"note\">文件切塊、向量化與 Parquet 儲存</tspan>
</text>

<rect class=\"module support\" x=\"420\" y=\"520\" width=\"260\" height=\"130\" />
<text text-anchor=\"middle\">
  <tspan x=\"550\" y=\"570\" class=\"label\">RAG Loader</tspan>
  <tspan x=\"550\" y=\"596\" class=\"path\">app/rag_loader.py</tspan>
  <tspan x=\"550\" y=\"622\" class=\"note\">載入 FAISS 索引、檢索最相關知識</tspan>
</text>

<rect class=\"module support\" x=\"750\" y=\"520\" width=\"240\" height=\"130\" />
<text text-anchor=\"middle\">
  <tspan x=\"870\" y=\"570\" class=\"label\">Utilities</tspan>
  <tspan x=\"870\" y=\"596\" class=\"path\">app/utils.py</tspan>
  <tspan x=\"870\" y=\"622\" class=\"note\">Gemini API 包裝與共用工具</tspan>
</text>

<!-- Worker -->
<rect class=\"module worker\" x=\"990\" y=\"520\" width=\"220\" height=\"130\" />
<text text-anchor=\"middle\">
  <tspan x=\"1100\" y=\"570\" class=\"label\">Automation Worker</tspan>
  <tspan x=\"1100\" y=\"596\" class=\"path\">app/iot/automation.py</tspan>
  <tspan x=\"1100\" y=\"622\" class=\"note\">Redis 任務監聽與規則觸發</tspan>
</text>

<!-- Redis Queue -->
<ellipse class=\"queue\" cx=\"1040\" cy=\"380\" rx=\"85\" ry=\"45\" />
<text text-anchor=\"middle\">
  <tspan x=\"1040\" y=\"378\" class=\"label\">Redis Queue</tspan>
  <tspan x=\"1040\" y=\"404\" class=\"note\">app/simple_queue.py</tspan>
</text>

<!-- Relationships -->
<path class=\"arrow\" d=\"M205 280 C 205 330, 360 340, 470 360\" />
<path class=\"arrow\" d=\"M605 280 L 610 340\" />
<path class=\"arrow\" d=\"M995 280 C 920 330, 820 340, 750 360\" />
<path class=\"arrow\" d=\"M330 585 L 420 585\" />
<path class=\"arrow\" d=\"M550 520 C 560 420, 580 330, 600 280\" />
<path class=\"arrow\" d=\"M870 520 C 820 450, 760 360, 720 320\" />
<path class=\"arrow\" d=\"M995 280 L 1035 335\" />
<path class=\"arrow\" d=\"M1035 425 L 1095 520\" />
<path class=\"arrow\" d=\"M1095 520 C 960 470, 820 410, 750 400\" />

<text x=\"360\" y=\"330\" class=\"accent\">SQLAlchemy 操作</text>
<text x=\"700\" y=\"360\" class=\"accent\">狀態更新</text>
<text x=\"360\" y=\"560\" class=\"accent\">文件 → 向量索引</text>
<text x=\"710\" y=\"470\" class=\"accent\">Gemini 輔助推論</text>
<text x=\"1025\" y=\"320\" class=\"accent\">任務入列</text>
<text x=\"1100\" y=\"470\" class=\"accent\">自動化處理</text>

</svg>"""

    output_path = output_dir / "backend_class_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path


def generate_frontend_component_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1300\" height=\"720\" viewBox=\"0 0 1300 720\">
<style>
  text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }
  .title { font-size: 30px; font-weight: bold; }
  .section { fill: #f5f9ff; stroke: #b0bec5; stroke-dasharray: 12 8; stroke-width: 2; rx: 22; ry: 22; }
  .module { fill: #ffffff; stroke-width: 2.6; rx: 18; ry: 18; }
  .view { stroke: #00897b; }
  .store { stroke: #5e35b1; }
  .api { stroke: #1e88e5; }
  .label { font-size: 22px; font-weight: 600; }
  .path { font-size: 16px; fill: #424242; }
  .note { font-size: 15px; fill: #616161; }
  .arrow { stroke: #546e7a; stroke-width: 2.5; fill: none; marker-end: url(#arrowhead); }
  .dashed { stroke-dasharray: 8 6; }
</style>
<defs>
  <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">
    <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#546e7a\" />
  </marker>
</defs>
<rect width=\"100%\" height=\"100%\" fill=\"#f0f4f8\" />
<text x=\"650\" y=\"55\" text-anchor=\"middle\" class=\"title\">前端元件架構圖 - Goat Nutrition</text>

<!-- Sections -->
<rect class=\"section\" x=\"80\" y=\"110\" width=\"360\" height=\"520\" />
<text x=\"260\" y=\"150\" text-anchor=\"middle\" class=\"note\">Views</text>

<rect class=\"section\" x=\"470\" y=\"110\" width=\"360\" height=\"520\" />
<text x=\"650\" y=\"150\" text-anchor=\"middle\" class=\"note\">Pinia Stores</text>

<rect class=\"section\" x=\"860\" y=\"110\" width=\"360\" height=\"520\" />
<text x=\"1040\" y=\"150\" text-anchor=\"middle\" class=\"note\">API Layer</text>

<!-- Views -->
<rect class=\"module view\" x=\"120\" y=\"210\" width=\"280\" height=\"140\" />
<text text-anchor=\"middle\">
  <tspan x=\"260\" y=\"260\" class=\"label\">SheepListView</tspan>
  <tspan x=\"260\" y=\"288\" class=\"path\">views/SheepListView.vue</tspan>
  <tspan x=\"260\" y=\"316\" class=\"note\">渲染羊群列表，透過 store 讀/寫資料</tspan>
</text>

<rect class=\"module view\" x=\"120\" y=\"400\" width=\"280\" height=\"140\" />
<text text-anchor=\"middle\">
  <tspan x=\"260\" y=\"450\" class=\"label\">DashboardView</tspan>
  <tspan x=\"260\" y=\"478\" class=\"path\">views/DashboardView.vue</tspan>
  <tspan x=\"260\" y=\"506\" class=\"note\">儀表板聚合數據，直接呼叫 API</tspan>
</text>

<!-- Stores -->
<rect class=\"module store\" x=\"510\" y=\"200\" width=\"280\" height=\"150\" />
<text text-anchor=\"middle\">
  <tspan x=\"650\" y=\"250\" class=\"label\">Auth Store</tspan>
  <tspan x=\"650\" y=\"278\" class=\"path\">stores/auth.js</tspan>
  <tspan x=\"650\" y=\"306\" class=\"note\">管理 Token 與登入狀態</tspan>
</text>

<rect class=\"module store\" x=\"510\" y=\"400\" width=\"280\" height=\"150\" />
<text text-anchor=\"middle\">
  <tspan x=\"650\" y=\"450\" class=\"label\">Sheep Store</tspan>
  <tspan x=\"650\" y=\"478\" class=\"path\">stores/sheep.js</tspan>
  <tspan x=\"650\" y=\"506\" class=\"note\">封裝羊群 API 呼叫與狀態</tspan>
</text>

<!-- API Client -->
<rect class=\"module api\" x=\"900\" y=\"300\" width=\"280\" height=\"160\" />
<text text-anchor=\"middle\">
  <tspan x=\"1040\" y=\"350\" class=\"label\">API Client</tspan>
  <tspan x=\"1040\" y=\"378\" class=\"path\">api/index.js</tspan>
  <tspan x=\"1040\" y=\"406\" class=\"note\">集中管理 Axios 請求與錯誤處理</tspan>
</text>

<!-- Relationships -->
<path class=\"arrow\" d=\"M400 290 L 510 290\" />
<text x=\"450\" y=\"270\" class=\"note\">使用 actions</text>

<path class=\"arrow\" d=\"M400 470 L 900 360\" />
<text x=\"650\" y=\"360\" class=\"note\">直接呼叫 API Client</text>

<path class=\"arrow\" d=\"M790 470 L 900 380\" />
<text x=\"820\" y=\"430\" class=\"note\">封裝 API 呼叫</text>

<path class=\"arrow dashed\" d=\"M790 250 L 900 330\" />
<text x=\"830\" y=\"300\" class=\"note\">附加認證標頭</text>

<path class=\"arrow\" d=\"M260 400 L 260 350\" marker-end=\"url(#arrowhead)\" />
<text x=\"180\" y=\"370\" class=\"note\">列表更新</text>

<path class=\"arrow dashed\" d=\"M260 180 C 260 150, 650 150, 650 180\" />
<text x=\"650\" y=\"140\" class=\"note\">登入狀態提供給視圖</text>

</svg>"""

    output_path = output_dir / "frontend_component_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path

def generate_auth_subsystem_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1180\" height=\"620\" viewBox=\"0 0 1180 620\">\n  <style>\n    text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }\n    .title { font-size: 28px; font-weight: bold; }\n    .section { fill: #eef5ff; stroke: #90a4ae; stroke-dasharray: 10 6; stroke-width: 2; rx: 18; ry: 18; }\n    .module { fill: #ffffff; stroke-width: 2.3; rx: 16; ry: 16; }\n    .backend { stroke: #1e88e5; }\n    .frontend { stroke: #00897b; }\n    .label { font-size: 20px; font-weight: 600; }\n    .note { font-size: 16px; fill: #546e7a; }\n    .arrow { stroke: #455a64; stroke-width: 2.2; fill: none; marker-end: url(#arrowhead); }\n  </style>\n  <defs>\n    <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">\n      <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#455a64\" />\n    </marker>\n  </defs>\n  <rect width=\"100%\" height=\"100%\" fill=\"#f3f6fb\" />\n  <text x=\"590\" y=\"50\" text-anchor=\"middle\" class=\"title\">子系統互動圖 - 認證與權限</text>\n\n  <rect class=\"section\" x=\"80\" y=\"110\" width=\"400\" height=\"440\" />\n  <text x=\"280\" y=\"140\" text-anchor=\"middle\" class=\"note\">前端模組</text>\n\n  <rect class=\"section\" x=\"600\" y=\"110\" width=\"500\" height=\"440\" />\n  <text x=\"850\" y=\"140\" text-anchor=\"middle\" class=\"note\">後端模組</text>\n\n  <rect class=\"module frontend\" x=\"120\" y=\"200\" width=\"320\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"280\" y=\"245\" class=\"label\">LoginView</tspan>\n    <tspan x=\"280\" y=\"273\" class=\"note\">前端登入/註冊介面</tspan>\n    <tspan x=\"280\" y=\"301\" class=\"note\">views/LoginView.vue</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"120\" y=\"360\" width=\"320\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"280\" y=\"405\" class=\"label\">Auth Store</tspan>\n    <tspan x=\"280\" y=\"433\" class=\"note\">stores/auth.js</tspan>\n    <tspan x=\"280\" y=\"461\" class=\"note\">管理 token、登入狀態</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"650\" y=\"260\" width=\"400\" height=\"140\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"850\" y=\"305\" class=\"label\">Auth API</tspan>\n    <tspan x=\"850\" y=\"333\" class=\"note\">app/api/auth.py</tspan>\n    <tspan x=\"850\" y=\"361\" class=\"note\">登入、登出、註冊、Session 驗證</tspan>
</text>

  <path class=\"arrow\" d=\"M440 255 L 650 305\" />
  <text x=\"540\" y=\"250\" class=\"note\">送出認證請求</text>

  <path class=\"arrow\" d=\"M440 415 L 650 325\" />
  <text x=\"540\" y=\"360\" class=\"note\">攜帶 token 驗證 Session</text>

  <path class=\"arrow\" d=\"M650 360 L 440 460\" />
  <text x=\"540\" y=\"420\" class=\"note\">回傳權限資訊</text>

  <path class=\"arrow\" d=\"M650 295 L 440 220\" />
  <text x=\"540\" y=\"210\" class=\"note\">多因子驗證挑戰</text>
  </svg>"""

    output_path = output_dir / "auth_subsystem_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path

def generate_flock_data_subsystem_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1220\" height=\"640\" viewBox=\"0 0 1220 640\">\n  <style>\n    text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }\n    .title { font-size: 28px; font-weight: bold; }\n    .section { fill: #f2f6ff; stroke: #90a4ae; stroke-dasharray: 10 6; stroke-width: 2; rx: 18; ry: 18; }\n    .module { fill: #ffffff; stroke-width: 2.3; rx: 16; ry: 16; }\n    .frontend { stroke: #00897b; }\n    .backend { stroke: #1e88e5; }\n    .data { stroke: #6c5ce7; }\n    .label { font-size: 20px; font-weight: 600; }\n    .note { font-size: 16px; fill: #546e7a; }\n    .arrow { stroke: #37474f; stroke-width: 2.2; fill: none; marker-end: url(#arrowhead); }\n    .dashed { stroke-dasharray: 8 6; }\n  </style>\n  <defs>\n    <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">\n      <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#37474f\" />\n    </marker>\n  </defs>\n  <rect width=\"100%\" height=\"100%\" fill=\"#f7f9fc\" />\n  <text x=\"610\" y=\"50\" text-anchor=\"middle\" class=\"title\">子系統互動圖 - 羊群與資料治理</text>\n\n  <rect class=\"section\" x=\"60\" y=\"110\" width=\"340\" height=\"460\" />\n  <text x=\"230\" y=\"140\" text-anchor=\"middle\" class=\"note\">前端 / 營運</text>\n\n  <rect class=\"section\" x=\"430\" y=\"110\" width=\"360\" height=\"460\" />\n  <text x=\"610\" y=\"140\" text-anchor=\"middle\" class=\"note\">後端服務</text>\n\n  <rect class=\"section\" x=\"820\" y=\"110\" width=\"320\" height=\"460\" />\n  <text x=\"980\" y=\"140\" text-anchor=\"middle\" class=\"note\">資料層</text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"200\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"245\" class=\"label\">SheepListView</tspan>\n    <tspan x=\"230\" y=\"273\" class=\"note\">views/SheepListView.vue</tspan>\n    <tspan x=\"230\" y=\"301\" class=\"note\">羊群清單 / 篩選</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"360\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"405\" class=\"label\">DataManagementView</tspan>\n    <tspan x=\"230\" y=\"433\" class=\"note\">views/DataManagementView.vue</tspan>\n    <tspan x=\"230\" y=\"461\" class=\"note\">批次匯入 / 清理</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"520\" width=\"280\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"560\" class=\"label\">Sheep Store</tspan>\n    <tspan x=\"230\" y=\"588\" class=\"note\">stores/sheep.js</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"460\" y=\"200\" width=\"300\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"610\" y=\"245\" class=\"label\">Sheep API</tspan>
    <tspan x=\"610\" y=\"273\" class=\"note\">app/api/sheep.py</tspan>
    <tspan x=\"610\" y=\"301\" class=\"note\">CRUD / 事件紀錄</tspan>
  </text>

  <rect class=\"module backend\" x=\"460\" y=\"350\" width=\"300\" height=\"130\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"610\" y=\"395\" class=\"label\">Data Management API</tspan>\n    <tspan x=\"610\" y=\"423\" class=\"note\">app/api/data_management.py</tspan>\n    <tspan x=\"610\" y=\"451\" class=\"note\">資料匯入 / 驗證</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"460\" y=\"510\" width=\"300\" height=\"100\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"610\" y=\"555\" class=\"label\">SQLAlchemy Models</tspan>\n    <tspan x=\"610\" y=\"583\" class=\"note\">app/models.py</tspan>\n  </text>\n\n  <rect class=\"module data\" x=\"850\" y=\"200\" width=\"260\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"980\" y=\"245\" class=\"label\">PostgreSQL / SQLite</tspan>\n    <tspan x=\"980\" y=\"273\" class=\"note\">農場主資料</tspan>\n  </text>\n\n  <rect class=\"module data\" x=\"850\" y=\"360\" width=\"260\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"980\" y=\"405\" class=\"label\">批次匯入緩衝</tspan>\n    <tspan x=\"980\" y=\"433\" class=\"note\">instance/app.db · Parquet</tspan>\n  </text>\n\n  <rect class=\"module data\" x=\"850\" y=\"520\" width=\"260\" height=\"100\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"980\" y=\"560\" class=\"label\">Audit Log</tspan>\n    <tspan x=\"980\" y=\"588\" class=\"note\">migrations / Alembic</tspan>\n  </text>\n\n  <path class=\"arrow\" d=\"M230 320 L 230 360\" />\n  <text x=\"240\" y=\"340\" class=\"note\">批次匯入</text>\n\n  <path class=\"arrow\" d=\"M230 520 L 230 470\" />\n  <text x=\"190\" y=\"500\" class=\"note\">快取列表</text>\n\n  <path class=\"arrow\" d=\"M370 260 L 460 260\" />\n  <text x=\"410\" y=\"240\" class=\"note\">REST 請求</text>\n\n  <path class=\"arrow dashed\" d=\"M370 420 L 460 420\" />\n  <text x=\"410\" y=\"400\" class=\"note\">CSV 上傳</text>\n\n  <path class=\"arrow\" d=\"M760 260 L 850 260\" />\n  <text x=\"800\" y=\"240\" class=\"note\">ORM 儲存</text>\n\n  <path class=\"arrow\" d=\"M760 420 L 850 420\" />\n  <text x=\"800\" y=\"400\" class=\"note\">暫存驗證</text>\n\n  <path class=\"arrow dashed\" d=\"M610 510 L 610 470\" />\n  <text x=\"630\" y=\"490\" class=\"note\">資料驗證</text>\n\n  <path class=\"arrow\" d=\"M980 320 L 980 360\" />\n  <text x=\"990\" y=\"340\" class=\"note\">定期備份</text>\n\n  <path class=\"arrow dashed\" d=\"M980 480 L 980 520\" />\n  <text x=\"990\" y=\"500\" class=\"note\">異動追蹤</text>\n  </svg>"""

    output_path = output_dir / "flock_data_subsystem_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path

def generate_ai_prediction_subsystem_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1240\" height=\"660\" viewBox=\"0 0 1240 660\">\n  <style>\n    text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }\n    .title { font-size: 28px; font-weight: bold; }\n    .section { fill: #f1f8e9; stroke: #9ccc65; stroke-dasharray: 10 6; stroke-width: 2; rx: 18; ry: 18; }\n    .module { fill: #ffffff; stroke-width: 2.4; rx: 16; ry: 16; }\n    .frontend { stroke: #43a047; }\n    .backend { stroke: #1e88e5; }\n    .external { stroke: #8e24aa; }\n    .model { stroke: #fb8c00; }\n    .label { font-size: 20px; font-weight: 600; }\n    .note { font-size: 16px; fill: #546e7a; }\n    .arrow { stroke: #37474f; stroke-width: 2.3; fill: none; marker-end: url(#arrowhead); }\n    .dashed { stroke-dasharray: 8 6; }\n  </style>\n  <defs>\n    <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">\n      <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#37474f\" />\n    </marker>\n  </defs>\n  <rect width=\"100%\" height=\"100%\" fill=\"#f9fbf4\" />\n  <text x=\"620\" y=\"50\" text-anchor=\"middle\" class=\"title\">子系統互動圖 - AI 與生長預測</text>\n\n  <rect class=\"section\" x=\"60\" y=\"110\" width=\"360\" height=\"480\" />\n  <text x=\"240\" y=\"140\" text-anchor=\"middle\" class=\"note\">前端互動</text>\n\n  <rect class=\"section\" x=\"450\" y=\"110\" width=\"360\" height=\"480\" />\n  <text x=\"630\" y=\"140\" text-anchor=\"middle\" class=\"note\">後端推論</text>\n\n  <rect class=\"section\" x=\"840\" y=\"110\" width=\"320\" height=\"480\" />\n  <text x=\"1000\" y=\"140\" text-anchor=\"middle\" class=\"note\">模型與外部資源</text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"200\" width=\"300\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"240\" y=\"245\" class=\"label\">PredictionView</tspan>\n    <tspan x=\"240\" y=\"273\" class=\"note\">views/PredictionView.vue</tspan>\n    <tspan x=\"240\" y=\"301\" class=\"note\">生長預測輸入</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"360\" width=\"300\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"240\" y=\"405\" class=\"label\">ChatView</tspan>\n    <tspan x=\"240\" y=\"433\" class=\"note\">views/ChatView.vue</tspan>\n    <tspan x=\"240\" y=\"461\" class=\"note\">AI 輔助問答</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"520\" width=\"300\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"240\" y=\"565\" class=\"label\">AI Stores</tspan>\n    <tspan x=\"240\" y=\"593\" class=\"note\">stores/prediction.js · stores/chat.js</tspan>\n    <tspan x=\"240\" y=\"621\" class=\"note\">管理請求狀態 / 緩存</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"480\" y=\"200\" width=\"300\" height=\"130\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"630\" y=\"245\" class=\"label\">Prediction API</tspan>\n    <tspan x=\"630\" y=\"273\" class=\"note\">app/api/prediction.py</tspan>\n    <tspan x=\"630\" y=\"301\" class=\"note\">推理 / 誤差回傳</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"480\" y=\"360\" width=\"300\" height=\"130\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"630\" y=\"405\" class=\"label\">Agent API</tspan>\n    <tspan x=\"630\" y=\"433\" class=\"note\">app/api/agent.py</tspan>\n    <tspan x=\"630\" y=\"461\" class=\"note\">RAG 聊天推理</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"480\" y=\"520\" width=\"300\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"630\" y=\"565\" class=\"label\">RAG Loader</tspan>\n    <tspan x=\"630\" y=\"593\" class=\"note\">app/rag_loader.py</tspan>\n  </text>\n\n  <rect class=\"module model\" x=\"870\" y=\"200\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1010\" y=\"245\" class=\"label\">Sheep Growth LGBM</tspan>\n    <tspan x=\"1010\" y=\"273\" class=\"note\">models/sheep_growth_lgbm_q10.joblib</tspan>\n  </text>\n\n  <rect class=\"module model\" x=\"870\" y=\"350\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1010\" y=\"395\" class=\"label\">特徵重要度</tspan>\n    <tspan x=\"1010\" y=\"423\" class=\"note\">models/sheep_feature_importances.csv</tspan>\n  </text>\n\n  <rect class=\"module external\" x=\"870\" y=\"500\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1010\" y=\"545\" class=\"label\">Gemini API</tspan>\n    <tspan x=\"1010\" y=\"573\" class=\"note\">Google Generative AI</tspan>\n  </text>\n\n  <path class=\"arrow\" d=\"M390 260 L 480 260\" />\n  <text x=\"420\" y=\"240\" class=\"note\">預測請求</text>\n\n  <path class=\"arrow\" d=\"M390 420 L 480 420\" />\n  <text x=\"420\" y=\"400\" class=\"note\">聊天查詢</text>\n\n  <path class=\"arrow\" d=\"M240 520 L 240 470\" />\n  <text x=\"180\" y=\"500\" class=\"note\">結果緩存</text>\n\n  <path class=\"arrow\" d=\"M780 260 L 870 260\" />\n  <text x=\"810\" y=\"240\" class=\"note\">模型推論</text>\n\n  <path class=\"arrow dashed\" d=\"M780 420 L 870 420\" />\n  <text x=\"810\" y=\"400\" class=\"note\">可解釋性資料</text>\n\n  <path class=\"arrow\" d=\"M780 560 L 870 560\" />\n  <text x=\"810\" y=\"540\" class=\"note\">語言推理</text>\n\n  <path class=\"arrow dashed\" d=\"M1010 320 L 1010 350\" />\n  <text x=\"1020\" y=\"335\" class=\"note\">週期更新</text>\n\n  <path class=\"arrow dashed\" d=\"M1010 470 L 1010 500\" />\n  <text x=\"1020\" y=\"485\" class=\"note\">RAG 上下文</text>\n\n  <path class=\"arrow\" d=\"M630 330 L 630 360\" />\n  <text x=\"640\" y=\"340\" class=\"note\">重試 / 限流</text>\n  </svg>"""

    output_path = output_dir / "ai_prediction_subsystem_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path

def generate_iot_automation_subsystem_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"660\" viewBox=\"0 0 1280 660\">\n  <style>\n    text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }\n    .title { font-size: 28px; font-weight: bold; }\n    .section { fill: #fff8e1; stroke: #ffb300; stroke-dasharray: 10 6; stroke-width: 2; rx: 18; ry: 18; }\n    .module { fill: #ffffff; stroke-width: 2.4; rx: 16; ry: 16; }\n    .frontend { stroke: #fb8c00; }\n    .backend { stroke: #1e88e5; }\n    .worker { stroke: #d84315; }\n    .device { stroke: #6d4c41; fill: #fbe9e7; }\n    .label { font-size: 20px; font-weight: 600; }\n    .note { font-size: 16px; fill: #546e7a; }\n    .arrow { stroke: #5d4037; stroke-width: 2.3; fill: none; marker-end: url(#arrowhead); }\n    .dashed { stroke-dasharray: 8 6; }\n  </style>\n  <defs>\n    <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">\n      <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#5d4037\" />\n    </marker>\n  </defs>\n  <rect width=\"100%\" height=\"100%\" fill=\"#fffdf6\" />\n  <text x=\"640\" y=\"50\" text-anchor=\"middle\" class=\"title\">子系統互動圖 - IoT 自動化</text>\n\n  <rect class=\"section\" x=\"60\" y=\"110\" width=\"320\" height=\"480\" />\n  <text x=\"220\" y=\"140\" text-anchor=\"middle\" class=\"note\">前端控制台</text>\n\n  <rect class=\"section\" x=\"410\" y=\"110\" width=\"320\" height=\"480\" />\n  <text x=\"570\" y=\"140\" text-anchor=\"middle\" class=\"note\">後端任務協調</text>\n\n  <rect class=\"section\" x=\"760\" y=\"110\" width=\"240\" height=\"480\" />\n  <text x=\"880\" y=\"140\" text-anchor=\"middle\" class=\"note\">工作佇列 / 工作者</text>\n\n  <rect class=\"section\" x=\"1030\" y=\"110\" width=\"200\" height=\"480\" />\n  <text x=\"1130\" y=\"140\" text-anchor=\"middle\" class=\"note\">現場裝置</text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"200\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"245\" class=\"label\">IotManagementView</tspan>\n    <tspan x=\"230\" y=\"273\" class=\"note\">views/IotManagementView.vue</tspan>\n    <tspan x=\"230\" y=\"301\" class=\"note\">裝置監控 / 任務派送</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"360\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"405\" class=\"label\">AutomationRuleBuilder</tspan>\n    <tspan x=\"230\" y=\"433\" class=\"note\">components/iot/AutomationRuleBuilder.vue</tspan>\n    <tspan x=\"230\" y=\"461\" class=\"note\">制定閾值 / 自動化</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"520\" width=\"280\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"560\" class=\"label\">IoT Store</tspan>\n    <tspan x=\"230\" y=\"588\" class=\"note\">stores/iot.js</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"440\" y=\"200\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"580\" y=\"245\" class=\"label\">IoT API</tspan>\n    <tspan x=\"580\" y=\"273\" class=\"note\">app/api/iot.py</tspan>\n    <tspan x=\"580\" y=\"301\" class=\"note\">裝置註冊 / 任務建立</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"440\" y=\"360\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"580\" y=\"405\" class=\"label\">Task Orchestrator</tspan>\n    <tspan x=\"580\" y=\"433\" class=\"note\">app/tasks.py</tspan>\n    <tspan x=\"580\" y=\"461\" class=\"note\">enqueue_iot_command</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"440\" y=\"520\" width=\"280\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"580\" y=\"560\" class=\"label\">Simple Queue</tspan>\n    <tspan x=\"580\" y=\"588\" class=\"note\">app/simple_queue.py</tspan>\n  </text>\n\n  <rect class=\"module worker\" x=\"780\" y=\"220\" width=\"200\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"880\" y=\"265\" class=\"label\">IoT Automation</tspan>\n    <tspan x=\"880\" y=\"293\" class=\"note\">app/iot/automation.py</tspan>\n    <tspan x=\"880\" y=\"321\" class=\"note\">自動化執行器</tspan>\n  </text>\n\n  <rect class=\"module worker\" x=\"780\" y=\"380\" width=\"200\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"880\" y=\"425\" class=\"label\">RQ Worker</tspan>\n    <tspan x=\"880\" y=\"453\" class=\"note\">backend/run_worker.py</tspan>\n    <tspan x=\"880\" y=\"481\" class=\"note\">Redis 任務消費</tspan>\n  </text>\n\n  <rect class=\"module device\" x=\"1050\" y=\"220\" width=\"160\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1130\" y=\"260\" class=\"label\">感測節點</tspan>\n    <tspan x=\"1130\" y=\"288\" class=\"note\">溫度 / 濕度</tspan>\n  </text>\n\n  <rect class=\"module device\" x=\"1050\" y=\"360\" width=\"160\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1130\" y=\"400\" class=\"label\">執行器</tspan>\n    <tspan x=\"1130\" y=\"428\" class=\"note\">餵食 / 通風控制</tspan>\n  </text>\n\n  <rect class=\"module device\" x=\"1050\" y=\"500\" width=\"160\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1130\" y=\"540\" class=\"label\">邊緣閘道</tspan>\n    <tspan x=\"1130\" y=\"568\" class=\"note\">MQTT / HTTPS</tspan>\n  </text>\n\n  <path class=\"arrow\" d=\"M230 320 L 230 360\" />\n  <text x=\"250\" y=\"340\" class=\"note\">建立規則</text>\n\n  <path class=\"arrow\" d=\"M230 480 L 230 520\" />\n  <text x=\"190\" y=\"500\" class=\"note\">狀態同步</text>\n\n  <path class=\"arrow\" d=\"M370 260 L 440 260\" />\n  <text x=\"400\" y=\"240\" class=\"note\">API 呼叫</text>\n\n  <path class=\"arrow dashed\" d=\"M370 420 L 440 420\" />\n  <text x=\"400\" y=\"400\" class=\"note\">規則上傳</text>\n\n  <path class=\"arrow\" d=\"M720 420 L 780 420\" />\n  <text x=\"750\" y=\"400\" class=\"note\">Redis 任務</text>\n\n  <path class=\"arrow\" d=\"M580 520 L 580 480\" />\n  <text x=\"600\" y=\"500\" class=\"note\">入列</text>\n\n  <path class=\"arrow\" d=\"M980 420 L 1050 420\" />\n  <text x=\"1000\" y=\"400\" class=\"note\">指令下達</text>\n\n  <path class=\"arrow dashed\" d=\"M1050 260 L 720 260\" />\n  <text x=\"900\" y=\"240\" class=\"note\">感測資料回報</text>\n\n  <path class=\"arrow dashed\" d=\"M1050 540 L 440 540\" />\n  <text x=\"760\" y=\"520\" class=\"note\">心跳 / 裝置狀態</text>\n\n  <path class=\"arrow\" d=\"M880 340 L 880 380\" />\n  <text x=\"890\" y=\"360\" class=\"note\">重試策略</text>\n  </svg>"""

    output_path = output_dir / "iot_automation_subsystem_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path

def generate_traceability_subsystem_diagram(output_dir: Path) -> Path:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1260\" height=\"640\" viewBox=\"0 0 1260 640\">\n  <style>\n    text { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; fill: #1b1b1b; }\n    .title { font-size: 28px; font-weight: bold; }\n    .section { fill: #e8f5fd; stroke: #29b6f6; stroke-dasharray: 10 6; stroke-width: 2; rx: 18; ry: 18; }\n    .module { fill: #ffffff; stroke-width: 2.3; rx: 16; ry: 16; }\n    .frontend { stroke: #0288d1; }\n    .backend { stroke: #1565c0; }\n    .data { stroke: #00acc1; }\n    .external { stroke: #00897b; }\n    .label { font-size: 20px; font-weight: 600; }\n    .note { font-size: 16px; fill: #546e7a; }\n    .arrow { stroke: #455a64; stroke-width: 2.2; fill: none; marker-end: url(#arrowhead); }\n    .dashed { stroke-dasharray: 8 6; }\n  </style>\n  <defs>\n    <marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"10\" refY=\"3.5\" orient=\"auto\">\n      <polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#455a64\" />\n    </marker>\n  </defs>\n  <rect width=\"100%\" height=\"100%\" fill=\"#f4fbff\" />\n  <text x=\"630\" y=\"50\" text-anchor=\"middle\" class=\"title\">子系統互動圖 - 產銷履歷</text>\n\n  <rect class=\"section\" x=\"60\" y=\"110\" width=\"320\" height=\"480\" />\n  <text x=\"220\" y=\"140\" text-anchor=\"middle\" class=\"note\">前端應用</text>\n\n  <rect class=\"section\" x=\"410\" y=\"110\" width=\"320\" height=\"480\" />\n  <text x=\"570\" y=\"140\" text-anchor=\"middle\" class=\"note\">後端服務</text>\n\n  <rect class=\"section\" x=\"760\" y=\"110\" width=\"250\" height=\"480\" />\n  <text x=\"885\" y=\"140\" text-anchor=\"middle\" class=\"note\">資料與稽核</text>\n\n  <rect class=\"section\" x=\"1040\" y=\"110\" width=\"180\" height=\"480\" />\n  <text x=\"1130\" y=\"140\" text-anchor=\"middle\" class=\"note\">外部利害關係人</text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"200\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"245\" class=\"label\">TraceabilityManagementView</tspan>\n    <tspan x=\"230\" y=\"273\" class=\"note\">views/TraceabilityManagementView.vue</tspan>\n    <tspan x=\"230\" y=\"301\" class=\"note\">批量維護批次資料</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"360\" width=\"280\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"405\" class=\"label\">TraceabilityPublicView</tspan>\n    <tspan x=\"230\" y=\"433\" class=\"note\">views/TraceabilityPublicView.vue</tspan>\n    <tspan x=\"230\" y=\"461\" class=\"note\">外部查詢公開資訊</tspan>\n  </text>\n\n  <rect class=\"module frontend\" x=\"90\" y=\"520\" width=\"280\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"230\" y=\"560\" class=\"label\">Traceability Store</tspan>\n    <tspan x=\"230\" y=\"588\" class=\"note\">stores/traceability.js</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"440\" y=\"200\" width=\"280\" height=\"130\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"580\" y=\"245\" class=\"label\">Traceability API</tspan>\n    <tspan x=\"580\" y=\"273\" class=\"note\">app/api/traceability.py</tspan>\n    <tspan x=\"580\" y=\"301\" class=\"note\">批次 / QR 代碼</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"440\" y=\"360\" width=\"280\" height=\"130\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"580\" y=\"405\" class=\"label\">Data Exporter</tspan>\n    <tspan x=\"580\" y=\"433\" class=\"note\">app/api/data_management.py</tspan>\n    <tspan x=\"580\" y=\"461\" class=\"note\">CSV/Excel 轉換</tspan>\n  </text>\n\n  <rect class=\"module backend\" x=\"440\" y=\"520\" width=\"280\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"580\" y=\"560\" class=\"label\">Audit Service</tspan>\n    <tspan x=\"580\" y=\"588\" class=\"note\">app/utils.py · logging</tspan>\n  </text>\n\n  <rect class=\"module data\" x=\"790\" y=\"200\" width=\"220\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"900\" y=\"245\" class=\"label\">Batch Ledger</tspan>\n    <tspan x=\"900\" y=\"273\" class=\"note\">PostgreSQL: traceability_batch</tspan>\n  </text>\n\n  <rect class=\"module data\" x=\"790\" y=\"360\" width=\"220\" height=\"120\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"900\" y=\"405\" class=\"label\">Document Archive</tspan>\n    <tspan x=\"900\" y=\"433\" class=\"note\">docs/assets/traceability</tspan>\n  </text>\n\n  <rect class=\"module data\" x=\"790\" y=\"520\" width=\"220\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"900\" y=\"560\" class=\"label\">Change Log</tspan>\n    <tspan x=\"900\" y=\"588\" class=\"note\">Alembic revisions</tspan>\n  </text>\n\n  <rect class=\"module external\" x=\"1060\" y=\"220\" width=\"140\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1130\" y=\"260\" class=\"label\">檢驗單位</tspan>\n    <tspan x=\"1130\" y=\"288\" class=\"note\">CSV 審核</tspan>\n  </text>\n\n  <rect class=\"module external\" x=\"1060\" y=\"360\" width=\"140\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1130\" y=\"400\" class=\"label\">消費者</tspan>\n    <tspan x=\"1130\" y=\"428\" class=\"note\">QR Code 查詢</tspan>\n  </text>\n\n  <rect class=\"module external\" x=\"1060\" y=\"500\" width=\"140\" height=\"110\" />\n  <text text-anchor=\"middle\">\n    <tspan x=\"1130\" y=\"540\" class=\"label\">合作通路</tspan>\n    <tspan x=\"1130\" y=\"568\" class=\"note\">資料 API</tspan>\n  </text>\n\n  <path class=\"arrow\" d=\"M230 320 L 230 360\" />\n  <text x=\"240\" y=\"340\" class=\"note\">公開資料</text>\n\n  <path class=\"arrow\" d=\"M370 260 L 440 260\" />\n  <text x=\"400\" y=\"240\" class=\"note\">批次維護</text>\n\n  <path class=\"arrow dashed\" d=\"M370 420 L 440 420\" />\n  <text x=\"400\" y=\"400\" class=\"note\">匯出 / 列印</text>\n\n  <path class=\"arrow\" d=\"M720 260 L 790 260\" />\n  <text x=\"760\" y=\"240\" class=\"note\">寫入帳冊</text>\n\n  <path class=\"arrow dashed\" d=\"M720 420 L 790 420\" />\n  <text x=\"760\" y=\"400\" class=\"note\">附件存證</text>\n\n  <path class=\"arrow\" d=\"M940 260 L 1060 260\" />\n  <text x=\"980\" y=\"240\" class=\"note\">審核通知</text>\n\n  <path class=\"arrow\" d=\"M940 420 L 1060 420\" />\n  <text x=\"980\" y=\"400\" class=\"note\">QR 查詢 JSON</text>\n\n  <path class=\"arrow dashed\" d=\"M940 560 L 1060 560\" />\n  <text x=\"980\" y=\"540\" class=\"note\">API Token</text>\n\n  <path class=\"arrow\" d=\"M580 330 L 580 360\" />\n  <text x=\"590\" y=\"340\" class=\"note\">稽核紀錄</text>\n  </svg>"""

    output_path = output_dir / "traceability_subsystem_diagram.svg"
    output_path.write_text(svg_content, encoding="utf-8")
    return output_path

def main() -> None:
    output_dir = Path(__file__).resolve().parent
    use_case_path = generate_use_case_diagram(output_dir)
    deployment_path = generate_deployment_diagram(output_dir)
    backend_path = generate_backend_class_diagram(output_dir)
    frontend_path = generate_frontend_component_diagram(output_dir)
    auth_path = generate_auth_subsystem_diagram(output_dir)
    flock_data_path = generate_flock_data_subsystem_diagram(output_dir)
    ai_prediction_path = generate_ai_prediction_subsystem_diagram(output_dir)
    iot_automation_path = generate_iot_automation_subsystem_diagram(output_dir)
    traceability_path = generate_traceability_subsystem_diagram(output_dir)
    print(f"Generated: {use_case_path}")
    print(f"Generated: {deployment_path}")
    print(f"Generated: {backend_path}")
    print(f"Generated: {frontend_path}")
    print(f"Generated: {auth_path}")
    print(f"Generated: {flock_data_path}")
    print(f"Generated: {ai_prediction_path}")
    print(f"Generated: {iot_automation_path}")
    print(f"Generated: {traceability_path}")


if __name__ == "__main__":
    main()
