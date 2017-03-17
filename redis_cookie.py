# coding: utf-8

from sanic_login import BaseSecurecookieSession
from itsdangerous import URLSafeTimedSerializer, BadSignature
from datetime import timedelta
from asyncio import get_event_loop, ensure_future
from sanic.response import json
from functools import wraps
from sanic.response import redirect
import logging
from http.cookies import SimpleCookie


def total_seconds(td):
    if not isinstance(td, timedelta):
        td = timedelta(seconds=td)
    return td.days * 60 * 60 * 24 + td.seconds


class RedisSecureCookie(BaseSecurecookieSession):

    redis_cookie_name = 'cook_keys'
    cookie_key_session = 'session'

    def __init__(self, redis_cookie_name=None, cookie_key_session=None, unauthorized_handler=None):
        self.redis_cookie_name = redis_cookie_name or self.redis_cookie_name
        self.cookie_key_session = cookie_key_session or self.cookie_key_session
        # the view handler to handle the unauthorized
        self.unauthorized_handlers = unauthorized_handler

    async def loads_cookie(self, request,  **kwargs):
        app_config = request.app.config
        session_cookie_value = request.headers.get("Cookie") or request.get('cookie')

        if session_cookie_value is None:
            return None
        s = self.get_signing_serializer(app_config)
        if s is None:
            return None
        max_age = total_seconds(app_config['permanent_session_lifetime'])

        cookie_ = SimpleCookie()
        cookie_.load(session_cookie_value)
        self._cookies = {name: cookie.value
                         for name, cookie in cookie_.items()}
        try:
            cookie_text_type = s.loads(self._cookies[self.cookie_key_session], max_age=max_age)
        except BadSignature as e:
            logging.info('decode the cookie error, info|{}'.format(str(e)))
            return None

        redis_cli = request.app.config.redis_cli
        if redis_cli is None:
            raise RuntimeError("No redis_cli param")

        # ret = await redis_cli.sismember(self.redis_cookie_name, cookie_text_type)
        ret = await  redis_cli.execute('sismember', self.redis_cookie_name, cookie_text_type)
        detail_control = self.authorize_handle(cookie_text_type)

        if ret == 1 and detail_control is True:
            return cookie_text_type

        return None

    @property
    def loop(self):
        return get_event_loop()

    def authorize_handle(self, cookie):
        """ control the detail power """
        return True

    def dumps_cookie(self, request, response, cookie,  **kwargs):
        redis_cli = request.app.config.redis_cli
        if self.cookie_key_session in response.cookies:
            return
        else:
            app_config = request.app.config
            s =  self.get_signing_serializer(app_config)
            value = s.dumps(cookie)
            """
            aioredis use the Future object to compatible the python3.4,
            uvloop.create_task is new funcion only support the  coroutines
            """
            # self.loop.create_task(redis_cli.execute('sadd', self.redis_cookie_name, cookie))
            ensure_future(redis_cli.execute('sadd', self.redis_cookie_name, cookie))

            response.cookies[self.cookie_key_session] = value

    def unauthize_handle(self, func):
        """
         this is the decorator to handle the the unauthorized
        """
        self.unauthorized_handlers = func
        return func

    def login_required(self, func):
        """
        this is only for function view handler, if you use the HttpMethod,
        please implement the decorator for class method.
        """
        @wraps(func)
        async def wrapper(request):
            cookie = await  self.loads_cookie(request)
            if cookie is None:
                if self.unauthorized_handlers is not None:
                    self.unauthorized_handlers()
                else:
                    return json('No auth', status=401)

            response = await func(request)
            self.dumps_cookie(request, response, cookie)
            return response

        return wrapper
