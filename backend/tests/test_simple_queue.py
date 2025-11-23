from app.simple_queue import SimpleJob, SimpleQueue, SimpleWorker


def sample_task(a, b):
    return a + b


def test_enqueue_and_fetch_job():
    queue = SimpleQueue()
    job = queue.enqueue(sample_task, 1, 2, description="addition")

    fetched = queue.fetch_job(job.id)
    assert fetched is job
    assert fetched.func_name.endswith("sample_task")


def test_worker_processes_jobs_and_burst():
    queue = SimpleQueue()
    results = []

    def collecting_task(value):
        results.append(value * 2)
        return value * 2

    queue.enqueue(collecting_task, 3)
    queue.enqueue(collecting_task, 4)

    worker = SimpleWorker(queue, sleep=0)
    worker.work(burst=True)

    assert results == [6, 8]
    assert queue.pop_job() is None


def test_simple_job_perform():
    job = SimpleJob(sample_task, (5, 7), {}, description=None)
    assert job.perform() == 12
    assert job.func_name.endswith("sample_task")
