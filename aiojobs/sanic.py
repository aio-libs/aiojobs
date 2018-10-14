# -*- coding: utf-8 -*-
from functools import wraps

from aiohttp.web import View

from . import create_scheduler

__all__ = ('setup', 'spawn', 'get_scheduler', 'get_scheduler_from_app')


def get_scheduler(request):
    scheduler = get_scheduler_from_request(request)
    if scheduler is None:
        raise RuntimeError(
            "Call aiojobs.sanic.setup() on application initialization")
    return scheduler


def get_scheduler_from_app(app):
    return app.AIOJOBS_SCHEDULER


def get_scheduler_from_request(request):
    return get_scheduler_from_app(request.app)


async def spawn(request, coro):
    return await get_scheduler(request).spawn(coro)


def setup(app, **kwargs):
    @app.listener('before_server_start')
    async def on_startup(app, loop):
        app.AIOJOBS_SCHEDULER = await create_scheduler(**kwargs)

    @app.listener('after_server_stop')
    async def on_cleanup(app, loop):
        await app.AIOJOBS_SCHEDULER.close()

