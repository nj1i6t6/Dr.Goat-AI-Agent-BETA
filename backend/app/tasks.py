"""背景任務與工作隊列工具"""
from __future__ import annotations

from typing import Any, Dict

from flask import current_app

from .simple_queue import SimpleQueue


def get_task_queue() -> SimpleQueue:
    """取得共用的 RQ 佇列實例。"""
    queue: SimpleQueue | None = current_app.extensions.get('rq_queue')  # type: ignore[assignment]
    if queue is None:
        redis_client = current_app.extensions.get('redis_client')
        if redis_client is None:  # pragma: no cover - 初始化問題應儘早暴露
            raise RuntimeError('Redis 尚未初始化，無法建立背景任務佇列')
        queue = SimpleQueue(current_app.config.get('RQ_QUEUE_NAME', 'default'), connection=redis_client)
        current_app.extensions['rq_queue'] = queue
    return queue


def example_generate_dashboard_snapshot(user_id: int) -> Dict[str, Any]:
    """示範性背景任務：針對指定使用者生成儀表板快照摘要。"""
    # 實務上可以在這裡整合報表或寄送通知
    return {
        'user_id': user_id,
        'status': 'generated',
    }


def enqueue_example_task(user_id: int):
    """將示範任務推送到背景佇列。"""
    queue = get_task_queue()
    return queue.enqueue(
        example_generate_dashboard_snapshot,
        user_id,
        description=f'Generate dashboard snapshot for user {user_id}',
    )


def verify_verifiable_log_chain() -> Dict[str, Any]:
    """執行完整的可驗證賬本鏈檢查。"""

    from app.services.verifiable_log_service import verify_chain  # 避免循環匯入

    result = verify_chain()
    if result['integrity'] == 'OK':
        current_app.logger.info(
            'Verifiable log integrity OK — %s entries checked',
            result.get('checked', 0),
        )
    else:
        current_app.logger.error(
            'Verifiable log integrity FAILED at id %s',
            result.get('broken_at_id'),
        )
    return result


def enqueue_verifiable_log_verification():
    """將可驗證賬本檢查排入背景任務。"""

    queue = get_task_queue()
    return queue.enqueue(
        verify_verifiable_log_chain,
        description='Verify verifiable ledger chain integrity',
    )
