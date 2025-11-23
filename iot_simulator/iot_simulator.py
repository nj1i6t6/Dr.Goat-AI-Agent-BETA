"""Simple IoT device simulator for sensing and control testing."""
from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Iterable, Optional

import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
LOGGER = logging.getLogger('iot-simulator')

DEFAULT_INGEST_URL = 'http://localhost:5000/api/iot/ingest'
DEFAULT_CONTROL_ROUTE = '/cmd'


@dataclass
class SimulatorConfig:
    api_key: str
    ingest_url: str = DEFAULT_INGEST_URL
    device_type: str = 'environment_sensor'
    interval_seconds: float = 15.0
    control_host: str = '0.0.0.0'
    control_port: int = 8080
    control_route: str = DEFAULT_CONTROL_ROUTE
    control_enabled: bool = True
    target_ear_nums: tuple[str, ...] = ()


def load_config() -> SimulatorConfig:
    api_key = os.getenv('API_KEY')
    if not api_key:
        raise RuntimeError('API_KEY 環境變數為必填，請提供後端裝置的 API Key')

    ingest_url = os.getenv('INGEST_URL', DEFAULT_INGEST_URL)
    device_type = os.getenv('DEVICE_TYPE', 'environment_sensor')
    interval = float(os.getenv('SEND_INTERVAL_SECONDS', '20'))
    control_url = os.getenv('CONTROL_URL')
    control_enabled = control_url is not None
    control_host = os.getenv('CONTROL_HOST', '0.0.0.0')
    control_port = int(os.getenv('CONTROL_PORT', '8080'))
    control_route = os.getenv('CONTROL_ROUTE', DEFAULT_CONTROL_ROUTE)
    ear_nums = tuple(filter(None, [value.strip() for value in os.getenv('TARGET_EAR_NUMS', '').split(',')]))

    return SimulatorConfig(
        api_key=api_key,
        ingest_url=ingest_url,
        device_type=device_type,
        interval_seconds=interval,
        control_host=control_host,
        control_port=control_port,
        control_route=control_route,
        control_enabled=control_enabled,
        target_ear_nums=ear_nums,
    )


def seasonal_offset() -> float:
    month = datetime.utcnow().month
    if month in {6, 7, 8}:  # 夏季
        return 4.0
    if month in {12, 1, 2}:  # 冬季
        return -3.0
    return 0.0


def random_choice(values: Iterable[str]) -> Optional[str]:
    options = list(values)
    if not options:
        return None
    return random.choice(options)


def build_payload_generator(device_type: str) -> Callable[[SimulatorConfig], Dict[str, float | int | str | bool]]:
    def environment_sensor(_: SimulatorConfig) -> Dict[str, float]:
        base_temp = 25.0 + seasonal_offset()
        return {
            'temperature': round(random.gauss(base_temp, 1.2), 2),
            'humidity': round(random.uniform(65, 85), 1),
            'ammonia_ppm': round(random.uniform(3, 12), 1),
            'co2_ppm': round(random.uniform(450, 800), 0),
            'noise_db': round(random.uniform(55, 70), 1),
        }

    def wearable_sensor(config: SimulatorConfig) -> Dict[str, float | int | bool | str]:
        ear_num = random_choice(config.target_ear_nums) or f'E{random.randint(100, 999)}'
        return {
            'ear_num': ear_num,
            'body_temperature': round(random.gauss(38.9, 0.3), 2),
            'activity_index': round(random.uniform(0.4, 1.5), 2),
            'rumination_minutes': random.randint(400, 520),
            'estrus_detected': random.random() > 0.92,
        }

    def feeder_sensor(config: SimulatorConfig) -> Dict[str, float | str]:
        ear_num = random_choice(config.target_ear_nums) or f'F{random.randint(100, 999)}'
        return {
            'ear_num': ear_num,
            'feed_intake_grams': round(random.uniform(1500, 2500), 0),
            'feeding_duration_seconds': random.randint(600, 1100),
        }

    def waterer_sensor(config: SimulatorConfig) -> Dict[str, float | str]:
        ear_num = random_choice(config.target_ear_nums) or f'W{random.randint(100, 999)}'
        return {
            'ear_num': ear_num,
            'water_intake_ml': round(random.uniform(3000, 5000), 0),
            'drinking_frequency': random.randint(8, 16),
        }

    def actuator_status(_: SimulatorConfig) -> Dict[str, str]:
        return {'state': random.choice(['idle', 'running', 'error'])}

    mapping: Dict[str, Callable[[SimulatorConfig], Dict[str, float | int | str | bool]]] = {
        'environment_sensor': environment_sensor,
        'wearable_tag': wearable_sensor,
        'smart_feeder': feeder_sensor,
        'smart_waterer': waterer_sensor,
        'actuator': actuator_status,
    }
    return mapping.get(device_type, environment_sensor)


def send_sensor_payload(config: SimulatorConfig, generator: Callable[[SimulatorConfig], Dict[str, float | int | str | bool]]) -> None:
    payload = {'data': generator(config)}
    try:
        response = requests.post(
            config.ingest_url,
            headers={'X-API-Key': config.api_key},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        LOGGER.info('已送出模擬數據: %s', json.dumps(payload))
    except Exception as exc:  # pragma: no cover - network errors are environment specific
        LOGGER.error('送出感測數據失敗: %s', exc)


def start_sensor_loop(config: SimulatorConfig) -> threading.Thread:
    generator = build_payload_generator(config.device_type)

    def _loop():
        while True:
            send_sensor_payload(config, generator)
            time.sleep(config.interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True, name='sensor-sender')
    thread.start()
    return thread


def create_control_app(config: SimulatorConfig) -> Flask:
    app = Flask(__name__)

    @app.post(config.control_route)
    def receive_command():  # type: ignore[override]
        payload = request.get_json(silent=True) or {}
        LOGGER.info('收到指令: %s', json.dumps(payload, ensure_ascii=False))
        return jsonify({'status': 'ok'}), 200

    @app.get('/healthz')
    def health():
        return jsonify({'status': 'ok'})

    return app


def run_control_server(app: Flask, config: SimulatorConfig) -> threading.Thread:
    def _run():
        LOGGER.info('控制指令伺服器啟動於 http://%s:%s%s', config.control_host, config.control_port, config.control_route)
        app.run(host=config.control_host, port=config.control_port)

    thread = threading.Thread(target=_run, daemon=True, name='control-server')
    thread.start()
    return thread


def main():
    config = load_config()
    LOGGER.info('啟動 IoT 模擬器，裝置類型: %s，資料間隔: %ss', config.device_type, config.interval_seconds)

    sender = start_sensor_loop(config)
    server_thread = None

    if config.control_enabled:
        control_app = create_control_app(config)
        server_thread = run_control_server(control_app, config)

    try:
        sender.join()
        if server_thread:
            server_thread.join()
    except KeyboardInterrupt:
        LOGGER.info('模擬器已停止')


if __name__ == '__main__':  # pragma: no cover - manual execution entry point
    main()
