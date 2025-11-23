from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.tasks import enqueue_example_task

bp = Blueprint('tasks', __name__)


@bp.route('/example', methods=['POST'])
@login_required
def enqueue_example_background_task():
    """觸發示範性背景任務。"""
    job = enqueue_example_task(current_user.id)
    return jsonify({
        'job_id': job.id,
        'status': 'queued',
    }), 202
