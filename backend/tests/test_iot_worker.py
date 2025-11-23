import json

import pytest

from app import db
from app.iot import CONTROL_QUEUE_KEY, SENSOR_QUEUE_KEY, process_control_command, process_sensor_payload
from app.models import AutomationRule, DeviceControlLog, IotDevice


@pytest.fixture
def sensor_and_actuator(app, test_user):
    with app.app_context():
        sensor = IotDevice(
            user_id=test_user.id,
            name='環境感測器',
            device_type='舍內環境監控',
            category='sensor',
            location='牛舍 A',
        )
        sensor.set_api_key('sensor-key')

        actuator = IotDevice(
            user_id=test_user.id,
            name='降溫風扇',
            device_type='自動風扇',
            category='actuator',
            control_url='http://localhost/mock',
        )
        actuator.set_api_key('actuator-key')

        db.session.add(sensor)
        db.session.add(actuator)
        db.session.flush()

        rule = AutomationRule(
            user_id=test_user.id,
            name='高溫自動開風扇',
            trigger_source_device_id=sensor.id,
            trigger_condition={'variable': 'temperature', 'operator': '>', 'value': 28},
            action_target_device_id=actuator.id,
            action_command={'command': 'turn_on', 'parameters': {'duration_minutes': 15}},
            is_enabled=True,
        )
        db.session.add(rule)
        db.session.commit()

        return sensor.id, actuator.id, rule.id


def test_process_sensor_payload_enqueues_command(app, sensor_and_actuator):
    sensor_id, actuator_id, rule_id = sensor_and_actuator
    with app.app_context():
        sensor = db.session.get(IotDevice, sensor_id)
    payload = {
        'device_id': sensor_id,
        'reading_id': 1,
        'user_id': sensor.user_id,
        'data': {'temperature': 30, 'humidity': 85},
        'received_at': '2024-08-20T12:00:00Z',
    }

    redis_client = app.extensions['redis_client']
    redis_client.delete(SENSOR_QUEUE_KEY)
    redis_client.delete(CONTROL_QUEUE_KEY)

    triggered = process_sensor_payload(app, payload)
    assert triggered is True

    command_raw = redis_client.lpop(CONTROL_QUEUE_KEY)
    assert command_raw is not None
    command_payload = json.loads(command_raw)
    assert command_payload['rule_id'] == rule_id
    assert command_payload['target_device_id'] == actuator_id
    assert command_payload['command']['command'] == 'turn_on'


def test_process_control_command_creates_log(app, sensor_and_actuator, monkeypatch):
    sensor_id, actuator_id, rule_id = sensor_and_actuator
    with app.app_context():
        actuator = db.session.get(IotDevice, actuator_id)
    redis_client = app.extensions['redis_client']
    redis_client.delete(CONTROL_QUEUE_KEY)

    command_payload = {
        'rule_id': rule_id,
        'target_device_id': actuator_id,
        'command': {'command': 'turn_on'},
        'trigger': {'device_id': sensor_id, 'value': 30},
    }

    def fake_post(url, json=None, timeout=10):
        class FakeResponse:
            ok = True
            status_code = 200
            text = 'ok'

        assert url == actuator.control_url
        assert json['command']['command'] == 'turn_on'
        return FakeResponse()

    success = process_control_command(app, command_payload, http_post=fake_post)
    assert success is True

    with app.app_context():
        logs = DeviceControlLog.query.filter_by(rule_id=rule_id).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.status == 'success'
        assert log.response_payload['status_code'] == 200

        actuator_refreshed = db.session.get(IotDevice, actuator_id)
        assert actuator_refreshed.status == 'online'


def test_process_control_command_handles_http_error(app, sensor_and_actuator):
    sensor_id, actuator_id, rule_id = sensor_and_actuator

    command_payload = {
        'rule_id': rule_id,
        'target_device_id': actuator_id,
        'command': {'command': 'turn_on'},
        'trigger': {'device_id': sensor_id, 'value': 30},
    }

    def failing_post(url, json=None, timeout=10):  # pragma: no cover - simple stub
        raise RuntimeError('network down')

    success = process_control_command(app, command_payload, http_post=failing_post)
    assert success is False

    with app.app_context():
        log = DeviceControlLog.query.filter_by(rule_id=rule_id).one()
        assert log.status == 'error'
        assert log.response_payload['error'] == 'network down'

        actuator = db.session.get(IotDevice, actuator_id)
        assert actuator.status != 'online'


def test_process_control_command_rolls_back_on_commit_failure(app, sensor_and_actuator, monkeypatch):
    sensor_id, actuator_id, rule_id = sensor_and_actuator

    command_payload = {
        'rule_id': rule_id,
        'target_device_id': actuator_id,
        'command': {'command': 'turn_on'},
        'trigger': {'device_id': sensor_id, 'value': 30},
    }

    original_rollback = db.session.rollback
    rollback_called = {'value': False}

    def failing_commit():
        raise RuntimeError('db unavailable')

    def tracking_rollback():
        rollback_called['value'] = True
        return original_rollback()

    monkeypatch.setattr(db.session, 'commit', failing_commit)
    monkeypatch.setattr(db.session, 'rollback', tracking_rollback)

    success = process_control_command(app, command_payload)
    assert success is False
    assert rollback_called['value'] is True

    with app.app_context():
        assert DeviceControlLog.query.count() == 0
