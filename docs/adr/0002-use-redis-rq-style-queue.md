# ADR 0002: Use Redis-backed lightweight queue instead of Celery

## Background
Incoming workloads include periodic report generation, notification fan-out, and IoT data ingest buffering. The team previously evaluated Celery but found it heavy for the project's deployment footprint and overkill for the current task throughput. Redis is already provisioned for caching and session storage.

## Decision
Adopt a lightweight RQ-style queue implemented in `backend/app/tasks.py` using Redis lists. Workers (`backend/run_worker.py`) poll Redis, deserialize jobs, and execute Python callables without introducing Celery or RabbitMQ.

## Consequences
- **Positive**: Reuses the existing Redis infrastructure, keeps operational complexity low, and allows faster cold starts in Docker containers.
- **Negative**: Lacks advanced scheduling, monitoring dashboards, and retry policies provided by Celery, so we must document retry/backoff patterns and implement them manually when needed.
