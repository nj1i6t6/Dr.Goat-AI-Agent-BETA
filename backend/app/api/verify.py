from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.verifiable_log_service import (
    append_event,  # noqa: F401 - re-export for future extensions
    list_entity_entries,
    recent_entries,
    verify_chain,
)

bp = Blueprint('verify', __name__)


@bp.route('/chain', methods=['GET'])
@login_required
def get_chain_status():
    start_id = request.args.get('start_id', type=int)
    limit = request.args.get('limit', type=int)
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id', type=int)
    include_entries = request.args.get('include_entries', 'false').lower() == 'true'

    result = verify_chain(start_id=start_id, limit=limit)

    if entity_type and entity_id is not None:
        entries = list_entity_entries(entity_type, entity_id, user_id=current_user.id)
        if entries is None:
            return jsonify(error='找不到資料或您沒有權限'), 404
        result['entries'] = entries
    elif include_entries:
        recent_limit = limit or 100
        result['entries'] = recent_entries(recent_limit, user_id=current_user.id)

    status_code = 200 if result['integrity'] == 'OK' else 409
    return jsonify(result), status_code
