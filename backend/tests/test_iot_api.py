import json

import pytest

from app import db
from app.iot import SENSOR_QUEUE_KEY
from app.models import IotDevice, SensorReading


@pytest.fixture
def create_device(authenticated_client):
    def _create(category='sensor', **overrides):
        payload = {
            'name': '測試裝置',
            'device_type': '環境感測器',
            'category': category,
            'location': 'A 區',
        }
        payload.update(overrides)
        response = authenticated_client.post('/api/iot/devices', json=payload)
        assert response.status_code == 201
        data = response.get_json()
        return data

    return _create


def test_device_crud_flow(authenticated_client, create_device):
    created = create_device()
    device_id = created['id']

    list_resp = authenticated_client.get('/api/iot/devices')
    assert list_resp.status_code == 200
    devices = list_resp.get_json()
    assert any(d['id'] == device_id for d in devices)
    assert all('api_key' not in d for d in devices)

    update_resp = authenticated_client.put(
        f'/api/iot/devices/{device_id}',
        json={'location': 'B 區', 'status': 'maintenance'},
    )
    assert update_resp.status_code == 200
    updated = update_resp.get_json()
    assert updated['location'] == 'B 區'
    assert updated['status'] == 'maintenance'

    delete_resp = authenticated_client.delete(f'/api/iot/devices/{device_id}')
    assert delete_resp.status_code == 200
    assert delete_resp.get_json()['success'] is True

    list_resp = authenticated_client.get('/api/iot/devices')
    assert list_resp.status_code == 200
    assert all(d['id'] != device_id for d in list_resp.get_json())


@pytest.mark.parametrize('missing_header', [None, ''])
def test_ingest_requires_api_key(client, missing_header):
    payload = {'data': {'temperature': 25}}
    headers = {}
    if missing_header is not None:
        headers['X-API-Key'] = missing_header
    resp = client.post('/api/iot/ingest', json=payload, headers=headers)
    assert resp.status_code == 401


def test_sensor_ingest_and_queue(app, authenticated_client, create_device):
    sensor = create_device()
    api_key = sensor['api_key']

    ingest_payload = {'data': {'temperature': 30.5, 'humidity': 82}}
    resp = authenticated_client.post(
        '/api/iot/ingest',
        json=ingest_payload,
        headers={'X-API-Key': api_key},
    )
    assert resp.status_code == 201

    with app.app_context():
        device = db.session.get(IotDevice, sensor['id'])
        assert device.status == 'online'
        assert device.api_key_digest == IotDevice.compute_digest(api_key)
        readings = SensorReading.query.filter_by(device_id=device.id).all()
        assert len(readings) == 1
        assert readings[0].data['temperature'] == 30.5

        redis_client = app.extensions['redis_client']
        queued = redis_client.lpop(SENSOR_QUEUE_KEY)
        assert queued is not None
        payload = json.loads(queued)
        assert payload['device_id'] == device.id
        assert payload['data']['humidity'] == 82


def test_ingest_rejects_invalid_key_without_leaking(client, caplog):
    caplog.set_level('WARNING')
    resp = client.post(
        '/api/iot/ingest',
        json={'data': {'temperature': 22}},
        headers={'X-API-Key': 'invalid-key'},
    )
    assert resp.status_code == 401
    assert all('invalid-key' not in record.getMessage() for record in caplog.records)
    assert all('digest' not in record.getMessage().lower() for record in caplog.records)


def test_automation_rule_lifecycle(app, authenticated_client, create_device, monkeypatch):
    sensor = create_device()
    actuator = create_device(category='actuator', device_type='自動風扇', control_url='http://localhost/cmd')

    rule_payload = {
        'name': '高溫開啟風扇',
        'trigger_source_device_id': sensor['id'],
        'trigger_condition': {'variable': 'temperature', 'operator': '>', 'value': 28},
        'action_target_device_id': actuator['id'],
        'action_command': {'command': 'turn_on', 'parameters': {'duration_minutes': 10}},
    }

    create_resp = authenticated_client.post('/api/iot/rules', json=rule_payload)
    assert create_resp.status_code == 201
    rule_id = create_resp.get_json()['id']

    list_resp = authenticated_client.get('/api/iot/rules')
    assert list_resp.status_code == 200
    assert any(rule['id'] == rule_id for rule in list_resp.get_json())

    update_resp = authenticated_client.put(
        f'/api/iot/rules/{rule_id}',
        json={'is_enabled': False},
    )
    assert update_resp.status_code == 200
    assert update_resp.get_json()['is_enabled'] is False

    delete_resp = authenticated_client.delete(f'/api/iot/rules/{rule_id}')
    assert delete_resp.status_code == 200
    assert delete_resp.get_json()['success'] is True


def test_rule_validation_enforces_categories(authenticated_client, create_device):
    sensor = create_device()
    another_sensor = create_device()

    rule_payload = {
        'name': '錯誤規則',
        'trigger_source_device_id': sensor['id'],
        'trigger_condition': {'variable': 'temperature', 'operator': '>', 'value': 28},
        'action_target_device_id': another_sensor['id'],
        'action_command': {'command': 'noop'},
    }

    resp = authenticated_client.post('/api/iot/rules', json=rule_payload)
    assert resp.status_code == 400
    assert '致動器' in resp.get_json()['error']


def test_create_app_without_secret_fails(monkeypatch):
    monkeypatch.delenv('API_HMAC_SECRET', raising=False)
    monkeypatch.setenv('SECRET_KEY', 'test')
    monkeypatch.setenv('CORS_ORIGINS', '*')
    monkeypatch.setenv('GOOGLE_API_KEY', 'test')
    monkeypatch.setenv('USE_FAKE_REDIS_FOR_TESTS', '1')
    monkeypatch.setenv('DOTENV_PATH', 'NON_EXISTENT_.env')

    import importlib

    app_module = importlib.import_module('app.__init__')
    importlib.reload(app_module)

    with pytest.raises(RuntimeError):
        app_module.create_app()
