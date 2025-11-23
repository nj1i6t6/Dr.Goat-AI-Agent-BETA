"""Minimal Redis-backed session interface without external dependencies."""
from __future__ import annotations

import json
import typing as t
import uuid
from datetime import timedelta

from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict


class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial: t.Optional[dict] = None, sid: str | None = None, new: bool = False):
        def on_update(_: CallbackDict) -> None:
            self.modified = True

        super().__init__(initial, on_update)
        self.sid = sid or self._generate_sid()
        self.new = new
        self.modified = False

    @staticmethod
    def _generate_sid() -> str:
        return uuid.uuid4().hex


class RedisSessionInterface(SessionInterface):
    session_class = RedisSession

    def __init__(self, redis_client, prefix: str = "session:") -> None:
        self.redis = redis_client
        self.key_prefix = prefix

    def generate_sid(self) -> str:
        return uuid.uuid4().hex

    def get_redis_expiration_time(self, app, session):  # type: ignore[override]
        if session.permanent:
            lifetime = app.permanent_session_lifetime
        else:
            lifetime = timedelta(days=1)
        return lifetime

    def open_session(self, app, request):  # type: ignore[override]
        cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        sid = request.cookies.get(cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)

        stored = self.redis.get(self.key_prefix + sid)
        if stored:
            try:
                data = json.loads(stored)
            except json.JSONDecodeError:
                data = {}
            return self.session_class(data, sid=sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):  # type: ignore[override]
        domain = self.get_cookie_domain(app)
        cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        if not session:
            self.redis.delete(self.key_prefix + session.sid)
            response.delete_cookie(cookie_name, domain=domain)
            return

        expiration = self.get_expiration_time(app, session)
        redis_exp = self.get_redis_expiration_time(app, session)
        data = json.dumps(dict(session))
        self.redis.setex(self.key_prefix + session.sid, int(redis_exp.total_seconds()), data)

        response.set_cookie(
            cookie_name,
            session.sid,
            expires=expiration,
            httponly=True,
            secure=app.config.get('SESSION_COOKIE_SECURE', False),
            samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
            domain=domain,
        )
