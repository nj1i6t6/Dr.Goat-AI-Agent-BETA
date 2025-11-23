"""Automation helpers for IoT sensor ingestion and actuator control."""
from __future__ import annotations

import json
import logging
import operator
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import requests
from flask import current_app

from app import db
from app.models import AutomationRule, DeviceControlLog, IotDevice

SENSOR_QUEUE_KEY = 'iot:sensor_queue'
CONTROL_QUEUE_KEY = 'iot:control_queue'

_LOGGER = logging.getLogger(__name__)

_OPERATOR_MAPPING: Dict[str, Callable[[Any, Any], bool]] = {
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '=': operator.eq,
    '!=': operator.ne,
}


def _coerce_numeric(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _deserialize(value: Any) -> Dict[str, Any]:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode('utf-8')
    if isinstance(value, str):
        return json.loads(value)
    return value


def enqueue_sensor_payload(redis_client, payload: Dict[str, Any]) -> None:
    redis_client.rpush(SENSOR_QUEUE_KEY, json.dumps(payload))


def dequeue_sensor_payload(redis_client, timeout: int = 0) -> Optional[Dict[str, Any]]:
    result = redis_client.blpop(SENSOR_QUEUE_KEY, timeout=timeout)
    if not result:
        return None
    if isinstance(result, tuple) and len(result) == 2:
        _, data = result
    else:
        data = result
    return _deserialize(data)


def enqueue_control_command(redis_client, payload: Dict[str, Any]) -> None:
    redis_client.rpush(CONTROL_QUEUE_KEY, json.dumps(payload))


def dequeue_control_command(redis_client, timeout: int = 0) -> Optional[Dict[str, Any]]:
    result = redis_client.blpop(CONTROL_QUEUE_KEY, timeout=timeout)
    if not result:
        return None
    if isinstance(result, tuple) and len(result) == 2:
        _, data = result
    else:
        data = result
    return _deserialize(data)


def _evaluate_condition(actual_value: Any, operator_symbol: str, expected_value: Any) -> bool:
    comparator = _OPERATOR_MAPPING.get(operator_symbol)
    if comparator is None:
        raise ValueError(f'Unsupported operator: {operator_symbol}')

    actual_numeric = _coerce_numeric(actual_value)
    expected_numeric = _coerce_numeric(expected_value)
    try:
        return comparator(actual_numeric, expected_numeric)
    except Exception:
        # 回退至原始比較
        return comparator(actual_value, expected_value)


def process_sensor_payload(app, payload: Dict[str, Any]) -> bool:
    """Evaluate automation rules for the incoming sensor payload."""
    device_id = payload.get('device_id')
    if not device_id:
        _LOGGER.warning('Sensor payload missing device_id: %s', payload)
        return False

    with app.app_context():
        device: Optional[IotDevice] = db.session.get(IotDevice, device_id)
        if not device:
            _LOGGER.warning('Sensor payload references missing device %s', device_id)
            return False

        data = payload.get('data', {})
        triggered = False
        rules = AutomationRule.query.filter_by(
            trigger_source_device_id=device_id,
            is_enabled=True
        ).all()

        for rule in rules:
            condition = rule.trigger_condition or {}
            variable = condition.get('variable')
            operator_symbol = condition.get('operator')
            expected_value = condition.get('value')

            if not variable or operator_symbol is None:
                continue

            actual_value = data.get(variable)
            if actual_value is None:
                continue

            try:
                if not _evaluate_condition(actual_value, operator_symbol, expected_value):
                    continue
            except ValueError as exc:
                _LOGGER.error('Automation rule %s has invalid operator: %s', rule.id, exc)
                continue
            except Exception as exc:  # pragma: no cover - defensive guard
                _LOGGER.exception('Failed to evaluate rule %s: %s', rule.id, exc)
                continue
 
            command_payload = {
                'rule_id': rule.id,
                'target_device_id': rule.action_target_device_id,
                'user_id': rule.user_id,
                'command': rule.action_command,
                'trigger': {
                    'device_id': device_id,
                    'reading_id': payload.get('reading_id'),
                    'value': actual_value,
                    'condition': condition,
                    'received_at': payload.get('received_at'),
                },
            }
            enqueue_control_command(app.extensions['redis_client'], command_payload)
            triggered = True
 
        return triggered


def process_control_command(
    app,
    payload: Dict[str, Any],
    http_post: Optional[Callable[..., requests.Response]] = None,
) -> bool:
    """Dispatch an automation command to the target device and persist a log."""
    if http_post is None:
        http_post = requests.post

    rule_id = payload.get('rule_id')
    target_device_id = payload.get('target_device_id')
    command = payload.get('command')

    if not (rule_id and target_device_id and isinstance(command, dict)):
        _LOGGER.warning('Invalid control payload: %s', payload)
        return False

    with app.app_context():
        rule: Optional[AutomationRule] = db.session.get(AutomationRule, rule_id)
        device: Optional[IotDevice] = db.session.get(IotDevice, target_device_id)

        if not device or not rule:
            _LOGGER.warning('Control payload references missing rule/device (rule=%s, device=%s)', rule_id, target_device_id)
            return False

        log_entry = DeviceControlLog(
            rule_id=rule_id,
            target_device_id=target_device_id,
            command=command,
            status='pending',
            executed_at=datetime.utcnow(),
        )
        db.session.add(log_entry)

        response_payload: Dict[str, Any] | None = None
        status = 'skipped'

        if device.control_url:
            try:
                response = http_post(
                    device.control_url,
                    json={'command': command, 'metadata': payload.get('trigger')},
                    timeout=10,
                )
                response_payload = {
                    'status_code': response.status_code,
                    'text': response.text,
                }
                status = 'success' if response.ok else 'error'
            except Exception as exc:  # pragma: no cover - network failure guard
                current_app.logger.exception('Failed to deliver control command: %s', exc)
                response_payload = {'error': str(exc)}
                status = 'error'
        else:
            status = 'skipped'

        try:
            log_entry.status = status
            log_entry.response_payload = response_payload

            if status == 'success':
                device.status = 'online'

            db.session.commit()
        except Exception as exc:  # pragma: no cover - defensive rollback
            db.session.rollback()
            _LOGGER.exception('Failed to finalize control command (rule=%s device=%s): %s', rule_id, target_device_id, exc)
            return False

        return status == 'success'
