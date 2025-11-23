"""IoT module API endpoints for device and automation management."""
from __future__ import annotations

import secrets
from datetime import datetime
from typing import Dict, Optional

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError

from app import db
from app.iot import enqueue_sensor_payload
from app.models import AutomationRule, IotDevice, SensorReading
from app.schemas import (
    AutomationRuleCreateModel,
    AutomationRuleUpdateModel,
    IotDeviceCreateModel,
    IotDeviceUpdateModel,
    SensorIngestModel,
)

bp = Blueprint('iot', __name__)


def _device_to_response(device: IotDevice, include_secret: bool = False, api_key: Optional[str] = None) -> Dict:
    data = device.to_safe_dict()
    if include_secret and api_key:
        data['api_key'] = api_key
    return data


def _rule_to_response(rule: AutomationRule) -> Dict:
    return {
        'id': rule.id,
        'name': rule.name,
        'trigger_source_device_id': rule.trigger_source_device_id,
        'action_target_device_id': rule.action_target_device_id,
        'trigger_condition': rule.trigger_condition,
        'action_command': rule.action_command,
        'is_enabled': rule.is_enabled,
        'created_at': rule.created_at.isoformat() if rule.created_at else None,
        'updated_at': rule.updated_at.isoformat() if rule.updated_at else None,
    }


def _find_device_by_api_key(api_key: str) -> Optional[IotDevice]:
    if not api_key:
        return None
    digest = IotDevice.compute_digest(api_key)
    return IotDevice.query.filter_by(api_key_digest=digest).first()


@bp.route('/devices', methods=['GET'])
@login_required
def list_devices():
    devices = (
        IotDevice.query.filter_by(user_id=current_user.id)
        .order_by(IotDevice.created_at.desc())
        .all()
    )
    return jsonify([_device_to_response(device) for device in devices])


@bp.route('/devices/<int:device_id>', methods=['GET'])
@login_required
def retrieve_device(device_id: int):
    device = IotDevice.query.filter_by(user_id=current_user.id, id=device_id).first()
    if not device:
        return jsonify(error='找不到裝置或無權存取'), 404
    return jsonify(_device_to_response(device))


@bp.route('/devices', methods=['POST'])
@login_required
def create_device():
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400
    try:
        payload = IotDeviceCreateModel(**request.get_json())
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    api_key = payload.api_key or secrets.token_urlsafe(24)
    device = IotDevice(
        user_id=current_user.id,
        name=payload.name,
        device_type=payload.device_type,
        category=payload.category,
        location=payload.location,
        control_url=payload.control_url,
        status=payload.status or 'offline',
    )
    device.set_api_key(api_key)

    db.session.add(device)
    db.session.commit()
    return jsonify(_device_to_response(device, include_secret=True, api_key=api_key)), 201


@bp.route('/devices/<int:device_id>', methods=['PUT'])
@login_required
def update_device(device_id: int):
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400

    device = IotDevice.query.filter_by(user_id=current_user.id, id=device_id).first()
    if not device:
        return jsonify(error='找不到裝置或無權存取'), 404

    try:
        payload = IotDeviceUpdateModel(**request.get_json())
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    update_data = payload.model_dump(exclude_unset=True)

    # 不允許直接透過此端點修改 API key
    for field, value in update_data.items():
        setattr(device, field, value)

    db.session.commit()
    return jsonify(_device_to_response(device))


@bp.route('/devices/<int:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id: int):
    device = IotDevice.query.filter_by(user_id=current_user.id, id=device_id).first()
    if not device:
        return jsonify(error='找不到裝置或無權存取'), 404

    db.session.delete(device)
    db.session.commit()
    return jsonify(success=True)


@bp.route('/devices/<int:device_id>/readings', methods=['GET'])
@login_required
def list_readings(device_id: int):
    device = IotDevice.query.filter_by(user_id=current_user.id, id=device_id).first()
    if not device:
        return jsonify(error='找不到裝置或無權存取'), 404

    limit = min(int(request.args.get('limit', 100)), 500)
    readings = (
        SensorReading.query.filter_by(device_id=device.id)
        .order_by(SensorReading.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify([
        {
            'id': reading.id,
            'data': reading.data,
            'created_at': reading.created_at.isoformat() if reading.created_at else None,
        }
        for reading in readings
    ])


@bp.route('/ingest', methods=['POST'])
def ingest_sensor_data():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify(error='缺少 X-API-Key 標頭'), 401
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400

    try:
        payload = SensorIngestModel(**request.get_json())
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    device = _find_device_by_api_key(api_key)
    if not device:
        current_app.logger.warning('Invalid API key used for ingestion')
        return jsonify(error='API Key 無效'), 401

    reading = SensorReading(device_id=device.id, data=payload.data)
    device.mark_seen()
    db.session.add(reading)
    db.session.commit()

    enqueue_sensor_payload(
        current_app.extensions['redis_client'],
        {
            'device_id': device.id,
            'reading_id': reading.id,
            'data': reading.data,
            'user_id': device.user_id,
            'received_at': reading.created_at.isoformat() if reading.created_at else datetime.utcnow().isoformat(),
        },
    )

    return jsonify(success=True), 201


@bp.route('/rules', methods=['GET'])
@login_required
def list_rules():
    rules = AutomationRule.query.filter_by(user_id=current_user.id).order_by(AutomationRule.created_at.desc()).all()
    return jsonify([_rule_to_response(rule) for rule in rules])


def _validate_rule_devices(trigger_device_id: int, action_device_id: int) -> Optional[str]:
    trigger_device = IotDevice.query.filter_by(user_id=current_user.id, id=trigger_device_id).first()
    if not trigger_device:
        return '觸發裝置不存在'
    if trigger_device.category != 'sensor':
        return '觸發裝置必須為感測器'

    action_device = IotDevice.query.filter_by(user_id=current_user.id, id=action_device_id).first()
    if not action_device:
        return '目標裝置不存在'
    if action_device.category != 'actuator':
        return '目標裝置必須為致動器'
    return None


@bp.route('/rules', methods=['POST'])
@login_required
def create_rule():
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400

    try:
        payload = AutomationRuleCreateModel(**request.get_json())
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    validation_error = _validate_rule_devices(payload.trigger_source_device_id, payload.action_target_device_id)
    if validation_error:
        return jsonify(error=validation_error), 400

    rule = AutomationRule(
        user_id=current_user.id,
        name=payload.name,
        trigger_source_device_id=payload.trigger_source_device_id,
        trigger_condition=payload.trigger_condition,
        action_target_device_id=payload.action_target_device_id,
        action_command=payload.action_command,
        is_enabled=payload.is_enabled if payload.is_enabled is not None else True,
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(_rule_to_response(rule)), 201


@bp.route('/rules/<int:rule_id>', methods=['PUT'])
@login_required
def update_rule(rule_id: int):
    rule = AutomationRule.query.filter_by(user_id=current_user.id, id=rule_id).first()
    if not rule:
        return jsonify(error='找不到規則或無權存取'), 404
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400

    try:
        payload = AutomationRuleUpdateModel(**request.get_json())
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    update_data = payload.model_dump(exclude_unset=True)

    trigger_id = update_data.get('trigger_source_device_id', rule.trigger_source_device_id)
    action_id = update_data.get('action_target_device_id', rule.action_target_device_id)
    validation_error = _validate_rule_devices(trigger_id, action_id)
    if validation_error:
        return jsonify(error=validation_error), 400

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.session.commit()
    return jsonify(_rule_to_response(rule))


@bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@login_required
def delete_rule(rule_id: int):
    rule = AutomationRule.query.filter_by(user_id=current_user.id, id=rule_id).first()
    if not rule:
        return jsonify(error='找不到規則或無權存取'), 404

    db.session.delete(rule)
    db.session.commit()
    return jsonify(success=True)
