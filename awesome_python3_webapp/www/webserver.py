import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time

from datetime import datetime
from Model import User
from aiohttp import web
from coreweb import get

@get('/')
def index(request):
    users = yield from User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }
    '''
    return web.Response(body="hello")
    '''
@asyncio.coroutine
def response_factory(app, handler):
    @asyncio.coroutine
    def response(request):
        r= yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'text/html;charset=utf-8'
            return resp

@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()