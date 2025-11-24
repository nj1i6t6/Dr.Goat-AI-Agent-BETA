"""RBAC 工具：提供農場層級的角色檢查。"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

from flask import jsonify
from flask_login import current_user

from .models import UserFarmRole

OWNER_ROLE = "Owner"
MANAGER_ROLE = "Manager"
WORKER_ROLE = "Worker"
VET_ROLE = "Vet"


def _get_membership(user_id: int, farm_id: int) -> UserFarmRole | None:
    return UserFarmRole.query.filter_by(user_id=user_id, farm_id=farm_id).first()


def role_required(roles: Iterable[str], farm_kw: str = "farm_id") -> Callable:
    """限制 API 只能由指定角色呼叫。

    Args:
        roles: 允許的角色列表。
        farm_kw: 從 view function kwargs 取得 farm id 的 key。
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify(error="Login required"), 401

            farm_id = kwargs.get(farm_kw)
            if farm_id is None:
                return jsonify(error="Farm context missing"), 400

            membership = _get_membership(current_user.id, farm_id)
            if membership is None:
                return jsonify(error="Farm membership required"), 403

            if membership.status != "active":
                return jsonify(error="Membership pending approval"), 403

            if membership.role not in roles and OWNER_ROLE not in roles and membership.role != OWNER_ROLE:
                return jsonify(error="Insufficient role"), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator

