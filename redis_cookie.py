# coding: utf-8

from sanic_login import BaseSecurecookieSession
from itsdangerous import URLSafeTimedSerializer, BadSignature
from datetime import timedelta
from asyncio import get_event_loop, ensure_future
from sanic.response import json
from functools import wraps


def total_seconds(td):
    if not isinstance(td, timedelta):
        td = timedelta(seconds=td)
    return td.days * 60 * 60 * 24 + td.seconds


class RedisSecureCookie(BaseSecurecookieSession):

    redis_cookie_name = 'cook_keys'

    def __init__(self, redis_cookie_name=None):
        self.redis_cookie_name = redis_cookie_name or self.redis_cookie_name

    async  def loads_cookie(self, request,  **kwargs):
        app_config = request.app.config
        session_cookie_value = request.headers.get("Cookie") or request.get('cookie')

        if session_cookie_value is None:
            print("no cookie")
            return None
        s = self.get_signing_serializer(app_config)
        if s is None:
            print("decode fail")
            return None
        max_age = total_seconds(app_config['permanent_session_lifetime'])
        # print("sess key", session_cookie_value)
        from http.cookies import SimpleCookie
        cookie_ = SimpleCookie()
        cookie_.load(session_cookie_value)
        self._cookies = {name: cookie.value
                         for name, cookie in cookie_.items()}
        print("sess key", self._cookies.get('session'))
        try:
            cookie_text_type = s.loads(self._cookies['session'], max_age=max_age)
        except BadSignature as e:

            print("BadSign", e)
            return None
        print("all cookie: ", self._cookies)
        redis_cli = request.app.config.redis_cli
        if redis_cli is None:
            raise RuntimeError("No redis_cli param")
        # ret = await redis_cli.sismember(self.redis_cookie_name, cookie_text_type)
        ret = await  redis_cli.execute('sismember', self.redis_cookie_name, cookie_text_type)
        print(ret)
        if ret == 1:
            return cookie_text_type
        else:
            return None

    @property
    def loop(self):
        return get_event_loop()

    def dumps_cookie(self, request, response, cookie,  **kwargs):
        redis_cli = request.app.config.redis_cli
        if 'session' in response.cookies:
            return
        else:
            app_config = request.app.config
            s =  self.get_signing_serializer(app_config)
            value = s.dumps(cookie)
            # self.loop.create_task(redis_cli.sadd(self.redis_cookie_name, cookie))
            # self.loop.create_task(redis_cli.execute('sadd', self.redis_cookie_name, cookie))
            ensure_future(redis_cli.execute('sadd', self.redis_cookie_name, cookie))
            response.cookies['session'] = value

    def login_required(self, func):
        """
        this is only for function view handler, if you use the HttpMethod,
        please implement the decorator for class method.
        """
        @wraps(func)
        async def wrapper(request):
            cookie = await  self.loads_cookie(request)
            if cookie is None:
                return json('No auth', status=401)

            response = await func(request)
            self.dumps_cookie(request, response, cookie)
            return response

        return wrapper


if __name__ == '__main__':
    a = {"a": 12}
    class B:
        def __init__(self, c):
            self.c = c
        def update(self):
            self.c['b'] = 'b'
    B(a).update()
    print(a)