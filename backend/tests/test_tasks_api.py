from app.tasks import enqueue_example_task, get_task_queue


def test_enqueue_example_task_endpoint(authenticated_client, app):
    response = authenticated_client.post('/api/tasks/example')
    assert response.status_code == 202
    payload = response.get_json()
    assert 'job_id' in payload
    with app.app_context():
        queue = get_task_queue()
        job = queue.fetch_job(payload['job_id'])
        assert job is not None
        assert job.kwargs == {}
        assert job.args[0] == 1  # authenticated_client fixture creates user id 1


def test_enqueue_example_task_direct(app):
    with app.app_context():
        job = enqueue_example_task(42)
        assert job.func_name.endswith('example_generate_dashboard_snapshot')
        assert job.args == (42,)
        result = job.perform()
        assert result['user_id'] == 42
        assert result['status'] == 'generated'
