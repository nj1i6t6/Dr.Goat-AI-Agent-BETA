from flask import Flask, request

from app.in_memory_redis import InMemoryRedis
from app.session_interface import RedisSessionInterface


def test_session_roundtrip_and_cleanup():
    app = Flask(__name__)
    app.config.update(SECRET_KEY="secret", SESSION_COOKIE_NAME="session")
    redis = InMemoryRedis()
    interface = RedisSessionInterface(redis)

    with app.test_request_context("/"):
        session = interface.open_session(app, request)
        assert session.new
        session["token"] = "abc"
        response = app.make_response("ok")
        interface.save_session(app, session, response)
        cookie_header = response.headers["Set-Cookie"]
        assert "session=" in cookie_header
        stored = redis.get(interface.key_prefix + session.sid)
        assert stored is not None

    cookie_value = cookie_header.split(";")[0].split("=", 1)[1]
    with app.test_request_context("/", headers={"Cookie": f"session={cookie_value}"}):
        session = interface.open_session(app, request)
        assert session["token"] == "abc"
        session.clear()
        response = app.make_response("bye")
        interface.save_session(app, session, response)
        assert redis.get(interface.key_prefix + session.sid) is None
        # cookie deletion should be signalled via header
        assert "session=" in response.headers.get("Set-Cookie", "")

    # 模擬快取中存有無效 JSON 的情況，open_session 應回傳新 session
    redis.set(interface.key_prefix + "corrupt", "{")
    with app.test_request_context("/", headers={"Cookie": "session=corrupt"}):
        session = interface.open_session(app, request)
        assert session.new is False
        assert dict(session) == {}

    # 直接呼叫 save_session 處理空 session，確保刪除邏輯覆蓋
    empty_session = interface.session_class(sid="empty", new=False)
    response = app.make_response("empty")
    interface.save_session(app, empty_session, response)
    assert redis.get(interface.key_prefix + empty_session.sid) is None
