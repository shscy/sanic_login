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


class UserMinx:
    def get_id(self):
        try:
            return self.id
        except AttributeError:
            raise NotImplementedError('No id attribute')

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def generate_cookie(self):
        """
        generate a unique cookie info which  has to be a instance of str or bytes
        here is a simple example
        """

        ret = self.get_id()
        if isinstance(ret, bytes) or isinstance(ret, str):
            return ret
        return TypeError("cookie info has to be a str or bytes")


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

    @classmethod
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
        """
        override the method to manager the login_cookie and session, authority, etc.
        """
        raise NotImplementedError

    def dumps_cookie(self, request, response, cookie,  **kwargs):
        """
        update the response cookie , then call create_task function to do some other things
        """
        raise NotImplementedError

    def authorize_handle(self, *args, **kwargs):
        """
        session and cookie  promise the user has logined,
        in here, you can control the the detail power of the user
        redis_cookie could be used for more web servers sharing
        the same Account, but each server has independent authority.
        so you can override this method
        """
        raise NotImplementedError



async def login_user(request, response, user_obj, redis_cookie):
    """ duck type """
    try:
        if not user_obj.is_active:
            return False

        redis_cli = request.app.config.redis_cli
        await redis_cli.execute('sadd', redis_cookie.redis_cookie_name, user_obj.generate_cookie)
        try:
            s = redis_cookie.get_signing_serializer(request.app.config)
            content = s.dumps(user_obj.generate_cookie)
            response.cookies[redis_cookie.] = content
        except:
            return False
        return True

    except AttributeError:
        raise TypeError("login_user accepts the parameter which is the instance of UserMinx or duck type")
    except TypeError as e:
        raise e


if __name__ == '__main__':
    a = BaseSecurecookieSession()
    b = a.get_signing_serializer({"secret_key": "gfegegewhfuengfengfengeng"})
    c = b.dumps("fewewgf")
    print(c)
    print(type(b.loads(c)))