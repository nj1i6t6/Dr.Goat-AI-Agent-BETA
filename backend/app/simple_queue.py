"""A minimal RQ-like queue implementation for demo and tests."""
from __future__ import annotations

import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, Optional


class SimpleJob:
    def __init__(self, func, args: tuple[Any, ...], kwargs: dict[str, Any], description: Optional[str]):
        self.id = uuid.uuid4().hex
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.description = description
        self.enqueued_at = time.time()
        self._result: Any = None

    @property
    def func_name(self) -> str:
        return f"{self.func.__module__}.{self.func.__name__}"

    def perform(self) -> Any:
        self._result = self.func(*self.args, **self.kwargs)
        return self._result


class SimpleQueue:
    def __init__(self, name: str = "default", connection: Any = None):
        self.name = name
        self.connection = connection
        self._jobs: Dict[str, SimpleJob] = {}
        self._pending: Deque[str] = deque()

    def enqueue(self, func, *args, description: Optional[str] = None, **kwargs) -> SimpleJob:
        job = SimpleJob(func, args, kwargs, description)
        self._jobs[job.id] = job
        self._pending.append(job.id)
        return job

    def fetch_job(self, job_id: str) -> Optional[SimpleJob]:
        return self._jobs.get(job_id)

    def pop_job(self) -> Optional[SimpleJob]:
        if not self._pending:
            return None
        job_id = self._pending.popleft()
        return self._jobs.get(job_id)


class SimpleWorker:
    def __init__(self, queue: SimpleQueue, sleep: float = 1.0):
        self.queue = queue
        self.sleep = sleep

    def work(self, burst: bool = False) -> None:
        while True:
            job = self.queue.pop_job()
            if job:
                job.perform()
                continue
            if burst:
                break
            time.sleep(self.sleep)
