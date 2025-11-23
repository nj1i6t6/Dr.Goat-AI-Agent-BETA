from flask import current_app

from app.in_memory_redis import InMemoryRedis
from app.tasks import enqueue_example_task, example_generate_dashboard_snapshot, get_task_queue


def test_get_task_queue_initializes_once(app):
    with app.app_context():
        current_app.extensions.pop('rq_queue', None)
        current_app.extensions['redis_client'] = InMemoryRedis()

        queue = get_task_queue()
        assert queue.name == current_app.config.get('RQ_QUEUE_NAME', 'default')

        # 第二次呼叫應回傳同一個實例
        assert get_task_queue() is queue


def test_enqueue_example_task(app):
    with app.app_context():
        current_app.extensions.pop('rq_queue', None)
        current_app.extensions['redis_client'] = InMemoryRedis()

        job = enqueue_example_task(user_id=123)
        assert job.func_name.endswith('example_generate_dashboard_snapshot')
        assert job.args == (123,)
        assert example_generate_dashboard_snapshot(123)['status'] == 'generated'
