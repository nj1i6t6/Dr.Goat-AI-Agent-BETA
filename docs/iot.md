# 智慧牧場 IoT 操作指南

本指南說明如何在系統內建立 IoT 裝置、串接模擬器並驗證自動化規則。建議先閱讀 [`docs/README.en.md`](./README.en.md#6-iot--automation-workflows) 取得整體架構概觀。

## 裝置型別速覽

前端 `frontend/src/stores/iot.js` 預載以下裝置型別與分類，可直接使用於建立裝置：

| 類別 | 型別名稱 | 代表用途 |
|------|----------|----------|
| 感測器 | 舍內環境監控 | 溫濕度、氨氣濃度監測 |
| 感測器 | 智慧頸圈/耳標 | 體溫、活動量、定位 |
| 感測器 | 電子藥丸/瘤胃監測器 | 反芻與腸胃狀態 |
| 感測器 | 自動體重計 | 體重走勢 |
| 感測器 | 自動化擠乳系統 | 乳量、乳成分 |
| 感測器 | 智慧採食槽 | 進食時段與份量 |
| 感測器 | 智慧飲水器 | 飲水頻率與容量 |
| 感測器 | 飼料/草料庫存感測器 | 庫存水位 |
| 感測器 | GPS 定位項圈 | 定位與移動軌跡 |
| 感測器 | AI 視覺攝影機 | 姿勢/健康偵測 |
| 致動器 | 自動分群門 | 依健康狀態分流 |
| 致動器 | 自動風扇 | 通風降溫 |
| 致動器 | 霧化降溫系統 | 降溫與環境控制 |
| 致動器 | 遮陽網/窗簾控制器 | 遮光、保溫 |
| 致動器 | 電磁閥 | 給水/給料管路控制 |
| 致動器 | 自動噴霧/消毒系統 | 疫病防治 |

## 建立裝置並取得 API Key

1. 以有權限帳號登入系統，開啟「智慧牧場 IoT」頁面。
2. 按「新增裝置」，填寫以下欄位：
   - **名稱**：內部辨識用途，例如「A 區智慧頸圈」。
   - **裝置型別**：自上述清單選擇，系統會自動設定分類。
   - **控制 URL（選填）**：若為致動器，可填入接收自動化指令的 HTTP Webhook。
3. 送出後，後端 `POST /api/iot/devices` 會產生一次性 API Key，對話框僅顯示一次明文。請立即妥善保存並寫入裝置端設定。

> 後端會以 `API_HMAC_SECRET` 對 API Key 做 HMAC 雜湊並存入 `api_key_digest`。若需重置，請刪除舊裝置並重新建立。

## 啟動模擬器傳送感測資料

專案提供 `iot_simulator/` 容器可模擬不同裝置。以下示範啟動一個智慧頸圈模擬器：

```bash
# 專案根目錄
cp .env.example .env  # 確保有 REDIS 與 API_HMAC_SECRET

# 於 docker-compose.yml 新增自訂服務（縮排與既有服務相同）
cat >> docker-compose.override.yml <<'YAML'
iot_simulator_wearable:
  build:
    context: ./iot_simulator
    dockerfile: Dockerfile
  environment:
    API_KEY: "<剛才複製的 API Key>"
    INGEST_URL: "http://backend:5001/api/iot/ingest"
    DEVICE_TYPE: "wearable_tag"
    SEND_INTERVAL_SECONDS: 25
  depends_on:
    - backend
  restart: unless-stopped
  networks:
    - goat-network
YAML

docker compose up --build -d iot_simulator_wearable
docker compose logs -f iot_simulator_wearable
```

日誌顯示 `已送出模擬數據` 即代表成功。裝置狀態會在後端 `device.mark_seen()` 後變為 Online。

## 驗證感測讀數與自動化

1. 在前端「智慧牧場 IoT」頁面點選剛建立的裝置，右側抽屜會顯示最近 `SensorReading`。可調整 `limit` 取得更多筆數。
2. 若需設定自動化規則，可於頁面切換至「自動化規則」分頁，或直接呼叫 API：

```bash
curl -X POST http://localhost:5001/api/iot/rules \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
        "name": "體溫過高開啟風扇",
        "trigger_source_device_id": 1,
        "action_target_device_id": 2,
        "trigger_condition": {"variable": "body_temperature", "operator": ">", "value": 39.5},
        "action_command": {"action": "turn_on", "speed": "high"}
      }'
```

3. 當模擬器送出的 `body_temperature` 高於 39.5 時，`app/iot/automation.py::process_sensor_payload` 會將命令寫入 `iot:control_queue`，並由 Worker 透過 `process_control_command` 建立 `DeviceControlLog`。若目標裝置設定了 `control_url`，還會同步觸發 HTTP POST。
4. 可透過 `docker compose logs backend` 或資料庫中的 `device_control_log` 表確認指令執行情況。

## 清除與重建

- 刪除裝置：`DELETE /api/iot/devices/{id}` 會連帶移除感測資料、規則與控制紀錄。
- 清空佇列：於 Python Shell 呼叫 `redis_client.delete('iot:sensor_queue', 'iot:control_queue')` 可重置佇列。
- 重建 API Key：目前僅支援刪除後重建。請更新設備端設定並重新部署模擬器。

完成上述流程即可快速驗證智慧牧場 IoT 管線與自動化邏輯，並在需要時擴充實體裝置整合。
