from __future__ import annotations

import secrets

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import MANAGER_ROLE, OWNER_ROLE, WORKER_ROLE, role_required
from app.models import Farm, User, UserFarmRole

bp = Blueprint('farm', __name__)


def _generate_farm_code() -> str:
    return secrets.token_hex(4).upper()


def _serialize_membership(membership: UserFarmRole) -> dict[str, object]:
    return {
        'id': membership.id,
        'farm_id': membership.farm_id,
        'role': membership.role,
        'status': membership.status,
    }


@bp.route('', methods=['GET'])
@login_required
def list_farms():
    memberships = UserFarmRole.query.filter_by(user_id=current_user.id).all()
    farm_ids = [m.farm_id for m in memberships]
    farms = Farm.query.filter(Farm.id.in_(farm_ids)).all() if farm_ids else []
    farm_map = {farm.id: farm for farm in farms}
    payload = []
    for membership in memberships:
        farm = farm_map.get(membership.farm_id)
        payload.append(
            {
                'farm': farm.to_dict() if farm else {'id': membership.farm_id},
                'membership': _serialize_membership(membership),
            }
        )
    return jsonify(payload)


@bp.route('', methods=['POST'])
@login_required
def create_farm():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(error='Farm name is required'), 400

    farm = Farm(name=name, code=_generate_farm_code(), owner_id=current_user.id)
    db.session.add(farm)
    db.session.flush()

    membership = UserFarmRole(
        user_id=current_user.id,
        farm_id=farm.id,
        role=OWNER_ROLE,
        status='active',
    )
    db.session.add(membership)
    db.session.commit()

    return jsonify(farm=farm.to_dict(), membership=_serialize_membership(membership)), 201


@bp.route('/join', methods=['POST'])
@login_required
def request_join():
    data = request.get_json(silent=True) or {}
    farm_code = (data.get('farm_code') or '').strip().upper()
    requested_role = (data.get('role') or WORKER_ROLE).title()

    farm = Farm.query.filter_by(code=farm_code).first()
    if not farm:
        return jsonify(error='Farm code not found'), 404

    existing = UserFarmRole.query.filter_by(user_id=current_user.id, farm_id=farm.id).first()
    if existing:
        return jsonify(membership=_serialize_membership(existing), farm=farm.to_dict()), 201

    membership = UserFarmRole(
        user_id=current_user.id,
        farm_id=farm.id,
        role=requested_role,
        status='pending',
    )
    db.session.add(membership)
    db.session.commit()
    return jsonify(membership=_serialize_membership(membership), farm=farm.to_dict()), 201


@bp.route('/<int:farm_id>/members/<int:membership_id>/approve', methods=['POST'])
@login_required
@role_required([OWNER_ROLE, MANAGER_ROLE])
def approve_member(farm_id: int, membership_id: int):
    data = request.get_json(silent=True) or {}
    role = (data.get('role') or WORKER_ROLE).title()

    membership = UserFarmRole.query.filter_by(id=membership_id, farm_id=farm_id).first()
    if not membership:
        return jsonify(error='Membership not found'), 404

    membership.role = role
    membership.status = 'active'
    db.session.commit()
    return jsonify(membership=_serialize_membership(membership))


@bp.route('/<int:farm_id>/members', methods=['GET'])
@login_required
@role_required([OWNER_ROLE, MANAGER_ROLE])
def list_members(farm_id: int):
    memberships = UserFarmRole.query.filter_by(farm_id=farm_id).all()
    user_ids = [m.user_id for m in memberships]
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    user_map = {user.id: user.username for user in users}
    payload = []
    for membership in memberships:
        payload.append(
            {
                'membership': _serialize_membership(membership),
                'username': user_map.get(membership.user_id),
            }
        )
    return jsonify(payload)

