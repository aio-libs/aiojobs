import asyncio

import pytest
from aiohttp import web

from aiojobs.aiohttp import setup as aiojobs_setup
from aiojobs.aiohttp import (atomic, get_scheduler, get_scheduler_from_app,
                             spawn)


async def test_plugin(test_client):
    job = None

    async def coro():
        await asyncio.sleep(10)

    async def handler(request):
        nonlocal job

        job = await spawn(request, coro())
        assert not job.closed
        return web.Response()

    app = web.Application()
    app.router.add_get('/', handler)
    aiojobs_setup(app)

    client = await test_client(app)
    resp = await client.get('/')
    assert resp.status == 200

    assert job.active
    await client.close()
    assert job.closed


async def test_no_setup(test_client):
    async def handler(request):
        with pytest.raises(RuntimeError):
            get_scheduler(request)
        return web.Response()

    app = web.Application()
    app.router.add_get('/', handler)

    client = await test_client(app)
    resp = await client.get('/')
    assert resp.status == 200


async def test_atomic(test_client):
    @atomic
    async def handler(request):
        await asyncio.sleep(0)
        return web.Response()

    app = web.Application()
    app.router.add_get('/', handler)
    aiojobs_setup(app)

    client = await test_client(app)
    resp = await client.get('/')
    assert resp.status == 200

    scheduler = get_scheduler_from_app(app)

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0


async def test_atomic_from_view(test_client):
    app = web.Application()

    class MyView(web.View):
        @atomic
        async def get(self):
            return web.Response()

    app.router.add_route("*", "/", MyView)
    aiojobs_setup(app)

    client = await test_client(app)
    resp = await client.get('/')
    assert resp.status == 200

    scheduler = get_scheduler_from_app(app)

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
