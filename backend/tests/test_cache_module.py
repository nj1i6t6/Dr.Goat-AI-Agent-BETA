from flask import current_app

from app.cache import clear_dashboard_cache, get_dashboard_cache, get_user_lock, set_dashboard_cache
from app.in_memory_redis import InMemoryRedis


def test_dashboard_cache_roundtrip(app):
    with app.app_context():
        redis = InMemoryRedis()
        current_app.extensions["redis_client"] = redis

        payload = {"value": 42}
        set_dashboard_cache(1, payload)
        assert get_dashboard_cache(1) == payload

        redis.set("dashboard-cache:1", "not-json")
        assert get_dashboard_cache(1) is None

        lock = get_user_lock(1)
        with lock:
            redis.set("dashboard-cache:1", "{}")

        clear_dashboard_cache(1)
        assert get_dashboard_cache(1) is None
