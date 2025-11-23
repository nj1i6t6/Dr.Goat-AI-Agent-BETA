import threading
import time

from app.in_memory_redis import InMemoryRedis


def test_set_get_delete_and_expiration():
    store = InMemoryRedis()
    store.set("key", "value")
    assert store.get("key") == "value"

    store.delete("key")
    assert store.get("key") is None

    store.setex("expire", 1, "soon-gone")
    assert store.get("expire") == "soon-gone"
    time.sleep(1.1)
    assert store.get("expire") is None


def test_lock_acquire_release():
    store = InMemoryRedis()
    lock1 = store.lock("resource", blocking_timeout=0.1)
    assert lock1.acquire()

    lock2 = store.lock("resource", blocking_timeout=0.1)
    assert lock2.acquire(blocking=False) is False

    lock1.release()
    assert lock2.acquire(blocking=True)
    lock2.release()


def test_queue_helpers():
    store = InMemoryRedis()
    assert store.lpop("queue") is None

    store.rpush("queue", "a", "b")
    assert store.lpop("queue") == "a"

    store.rpush("queue", "c")
    key, value = store.blpop("queue", timeout=1)
    assert key == "queue"
    assert value == "b"

    key, value = store.blpop("queue", timeout=1)
    assert (key, value) == ("queue", "c")
    assert store.blpop("queue", timeout=0.2) is None


def test_blpop_waits_until_available():
    store = InMemoryRedis()

    def delayed_push():
        time.sleep(0.2)
        store.rpush("queue", "later")

    thread = threading.Thread(target=delayed_push)
    thread.start()
    key, value = store.blpop("queue", timeout=1)
    thread.join()
    assert (key, value) == ("queue", "later")
