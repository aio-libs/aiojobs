import asyncio
from aiohttp import web
from aiojobs.aiohttp import setup as aiojobs_setup, spawn


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
