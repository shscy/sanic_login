# -*- coding: utf-8 -*-

from sanic import Sanic
from sanic.response import json
import asyncio
import asyncpg
import aioredis


app = Sanic(__name__)



@app.listener('before_server_start')
async def get_connect(app, loop):
    #conn = await asyncpg.connect(user='dbuser', password='password',
    #                             database='test', host='127.0.0.1')

    app.pool = await asyncpg.create_pool(database='test',
                        user='dbuser', password='password', host='127.0.0.1',
                                         min_size=100, max_size=200)
    app.config.redis_cli = await aioredis.create_connection(
        ('localhost', 6379), loop=loop)
    await app.config.redis_cli.execute('set', 'my-key', 'value')
    app.config.permanent_session_lifetime = 60*60*24*365
    app.config.secret_key = 'gfegegewhfuengfengfengeng'
    ret = await app.config.redis_cli.execute('get', 'my-key')
    print("redis test:", ret)
    # async with app.pool.acquire() as connection:
    #     # Open a transaction.
    #     async with connection.transaction():
    #         for i in range(10000, 100000):
    #             ret = await connection.execute('''insert into test_table(number, name) values ($1, $2);''', i, 'zuo')
    #             print("result", ret)



    # values = await conn.fetch('''SELECT * FROM mytable''')
    # await conn.close()
#conn_pool = get_connect()
import random
from redis_cookie import RedisSecureCookie
redis_secure_cookie = RedisSecureCookie()


@app.route("/api/", methods=('GET', 'POST'))
@redis_secure_cookie.login_required
async def test(request):

    async with request.app.pool.acquire() as connection:
        # Open a transaction.
        async with connection.transaction():
            # Run the query passing the request argument.
            #result = await connection.fetchval('select 2 ^ $1', power)
            # connection.
            num = random.randint(100, 9000)
            a = "select* from test_table where number = {}".format(num)
            print("num: ", num, a )
            values = await connection.fetch(a)
        # print("values", values)
    return json({ "hello": "world" })
app.run(host='0.0.0.0', port=8000, debug=True)

