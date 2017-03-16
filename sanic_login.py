# coding: utf-8
"""
the data stored in redis just like such {user_id: 'xxxx'}:
"""
from aioredis import  create_redis, create_pool
from itsdangerous import URLSafeTimedSerializer, BadSignature
import hashlib
import json
import uuid
from base64 import b64decode

iteritems = lambda x: iter(x.items())

class TaggedJSONSerializer(object):

    def dumps(self, value):
        return json.dumps(value, separators=(',', ':'))

    LOADS_MAP = {
        ' t': tuple,
        ' u': uuid.UUID,
        ' b': b64decode,
    }

    def loads(self, value):
        def object_hook(obj):
            if len(obj) != 1:
                return obj
            the_key, the_value = next(iteritems(obj))
            # Check the key for a corresponding function
            return_function = self.LOADS_MAP.get(the_key)
            if return_function:
                # Pass the value to the function
                return return_function(the_value)
            # Didn't find a function for this object
            return obj
        return json.loads(value, object_hook=object_hook)


session_json_serializer = TaggedJSONSerializer()


class BaseSecurecookieSession:
    salt = 'secure-cookie'
    digest_method = staticmethod(hashlib.sha1)
    key_derivation = 'hmac'
    serializer = session_json_serializer

    def get_signing_serializer(self, app):
        if not app['secret_key']:
            return None
        signer_kwargs = dict(
            key_derivation=self.key_derivation,
            digest_method=self.digest_method
        )
        return URLSafeTimedSerializer(app['secret_key'], salt=self.salt,
                                      serializer=self.serializer,
                                      signer_kwargs=signer_kwargs)


    def loads_cookie(self, request, **kwargs):
        """ 通过重写这个方法, 可以做到cookie的管理以及 权限的控制等等功能 """
        raise NotImplementedError

    def dumps_cookie(self, request, response, cookie,  **kwargs):
        """ 在这里只所以传入loop的值， 是因为在写入cookie的时候， 可以需要 会执行一些异步的任务等
            主要为了使用 loop.create_task
        """
        raise NotImplementedError


if __name__ == '__main__':
    a = BaseSecurecookieSession()
    b = a.get_signing_serializer({"secret_key": "gfegegewhfuengfengfengeng"})
    c = b.dumps("fewewgf")
    print(c)
    print(type(b.loads(c)))