# Codebase Metrics Summary

Generated: 2025-10-13T17:02:31.986797 UTC  
Directories scanned: `backend`, `frontend/src`, `scripts`, `iot_simulator`  
Extensions counted: `py`, `js`, `ts`, `tsx`, `vue`, `css`, `scss`, `html`

## Size Snapshot
- Source lines: 26,328
- Comment lines: 1,058
- Empty lines: 8,531
- Files counted: 198
- Estimated tokens (~60 chars/line, ~4 chars/token): ~394,920

## Language Breakdown
| Language | Files | Source LOC | Comment LOC | Empty LOC | Source Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| Python | 85 | 12,502 | 480 | 3,536 | 47.5% |
| Vue | 35 | 6,384 | 66 | 1,746 | 24.2% |
| JavaScript (templated) | 32 | 4,127 | 336 | 1,712 | 15.7% |
| JavaScript | 40 | 3,185 | 176 | 1,487 | 12.1% |
| CSS | 3 | 130 | 0 | 50 | 0.5% |

> Notes
> - pygount labels `.py` files as "IPython"; values are consolidated under **Python**.
> - "JavaScript (templated)" aggregates pygount categories that contain embedded template syntax (Genshi, Django/Jinja, Lasso).
> - Duplicate fixture files were skipped automatically by pygount.

## Python Complexity (radon cc)
- Average complexity: A (4.098191214470284)
- Blocks per grade: A: 646, B: 87, C: 30, D: 5, E: 2, F: 4
- Hot spots (top 10 by grade/score):
  - F (88): `backend\app\api\prediction.py` → `F 405:0 _compute_prediction_metrics`
  - F (56): `backend\app\api\data_management.py` → `F 458:0 process_import`
  - F (43): `backend\app\api\bi.py` → `F 265:0 _cost_benefit`
  - F (42): `backend\app\api\dashboard.py` → `F 15:0 get_dashboard_data`
  - E (35): `backend\app\api\bi.py` → `F 110:0 _cohort_analysis`
  - E (34): `backend\app\api\prediction.py` → `F 290:0 _normalize_category`
  - D (28): `backend\app\api\data_management.py` → `F 123:0 _validate_ai_mapping`
  - D (26): `backend\app\api\agent.py` → `F 449:0 chat_with_agent`
  - D (26): `backend\tests\test_prediction_api.py` → `M 11:4 TestPredictionAPI.test_get_prediction_success`
  - D (24): `backend\app\api\data_management.py` → `F 310:0 ai_import_mapping`

## Python Maintainability (radon mi)
- Files per grade: A: 81, B: 4, C: 1

## Raw Reports
- pygount JSON: `docs/code_metrics.json`
- radon cyclomatic complexity: `docs/radon_cc.txt`
- radon maintainability index: `docs/radon_mi.txt`

