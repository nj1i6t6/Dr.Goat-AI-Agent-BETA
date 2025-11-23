"""背景任務 Worker 啟動腳本，擴充 IoT 自動化流程。"""
from __future__ import annotations

import threading
import time

from app import create_app
from app.iot import dequeue_control_command, dequeue_sensor_payload, process_control_command, process_sensor_payload
from app.simple_queue import SimpleWorker


def _start_sensor_consumer(app):
    redis_client = app.extensions['redis_client']

    def _loop():
        while True:
            try:
                payload = dequeue_sensor_payload(redis_client, timeout=5)
                if payload:
                    process_sensor_payload(app, payload)
                else:
                    time.sleep(1)
            except Exception as exc:  # pragma: no cover - defensive guard
                app.logger.exception('Sensor consumer error: %s', exc)
                time.sleep(1)

    thread = threading.Thread(target=_loop, name='iot-sensor-consumer', daemon=True)
    thread.start()


def _start_control_consumer(app):
    redis_client = app.extensions['redis_client']

    def _loop():
        while True:
            try:
                payload = dequeue_control_command(redis_client, timeout=5)
                if payload:
                    process_control_command(app, payload)
                else:
                    time.sleep(1)
            except Exception as exc:  # pragma: no cover - defensive guard
                app.logger.exception('Control consumer error: %s', exc)
                time.sleep(1)

    thread = threading.Thread(target=_loop, name='iot-control-consumer', daemon=True)
    thread.start()


def main():
    app = create_app()
    with app.app_context():
        queue = app.extensions['rq_queue']
        worker = SimpleWorker(queue)
        _start_sensor_consumer(app)
        _start_control_consumer(app)
        worker.work()


if __name__ == '__main__':
    main()
