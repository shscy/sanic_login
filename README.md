## sanic_login

    基于URLSafeTimedSerializer的user session 管理插件。BaseSecurecookieSession类提供抽象方法。实现了redis作为存储中心，解决多个web服务共享同一套用户账号体系相关的权限问题。

## usage
    借鉴了flask_login的实现，在业务层非常易于使用。

    from redis_cookie import RedisSecureCookie
    redis_secure_cookie = RedisSecureCookie()
    
    @app.route("/api/", methods=('GET', 'POST'))
    @redis_secure_cookie.login_required
    async def test(request):
        return json({"a": "b"})
        
## TODO 
* 目前用户只有有权限和无权限两种状态，需要提供更多的状态控制

* sanic目前对cookie的支持还很基础， 更多对cookie的设置项还需完善
    
