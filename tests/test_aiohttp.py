import asyncio
from typing import Awaitable, Callable, Optional

import pytest
from aiohttp import ClientSession, ClientTimeout, web

# isort: off

from aiojobs.aiohttp import (
    atomic,
    get_scheduler,
    get_scheduler_from_app,
    get_scheduler_from_request,
    setup as aiojobs_setup,
    spawn,
)

# isort: on

_Client = Callable[[web.Application], Awaitable[ClientSession]]


async def test_plugin(aiohttp_client: _Client) -> None:
    job = None

    async def coro() -> None:
        await asyncio.sleep(10)

    async def handler(request: web.Request) -> web.Response:
        nonlocal job

        job = await spawn(request, coro())
        assert not job.closed
        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    aiojobs_setup(app)

    client = await aiohttp_client(app)
    resp = await client.get("/")
    assert resp.status == 200

    assert job is not None
    assert job.active
    await client.close()
    assert job.closed


async def test_no_setup(aiohttp_client: _Client) -> None:
    async def handler(request: web.Request) -> web.Response:
        with pytest.raises(RuntimeError):
            get_scheduler(request)
        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)

    client = await aiohttp_client(app)
    resp = await client.get("/")
    assert resp.status == 200


async def test_atomic(aiohttp_client: _Client) -> None:
    @atomic
    async def handler(request: web.Request) -> web.Response:
        await asyncio.sleep(0)
        return web.Response()

    app = web.Application()
    app.router.add_get("/", handler)
    aiojobs_setup(app)

    client = await aiohttp_client(app)
    resp = await client.get("/")
    assert resp.status == 200

    scheduler = get_scheduler_from_app(app)

    assert scheduler is not None
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0


async def test_atomic_from_view(aiohttp_client: _Client) -> None:
    app = web.Application()

    class MyView(web.View):
        @atomic
        async def get(self) -> web.Response:
            return web.Response(text=self.request.method)

    app.router.add_route("*", "/", MyView)
    aiojobs_setup(app)

    client = await aiohttp_client(app)
    resp = await client.get("/")
    assert resp.status == 200
    assert await resp.text() == "GET"

    scheduler = get_scheduler_from_app(app)

    assert scheduler is not None
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0


async def test_nested_application(aiohttp_client: _Client) -> None:
    app = web.Application()
    aiojobs_setup(app)

    app2 = web.Application()

    class MyView(web.View):
        async def get(self) -> web.Response:
            assert get_scheduler_from_request(self.request) == get_scheduler_from_app(
                app
            )
            return web.Response()

    app2.router.add_route("*", "/", MyView)
    app.add_subapp("/sub/", app2)

    client = await aiohttp_client(app)
    resp = await client.get("/sub/")
    assert resp.status == 200


async def test_nested_application_separate_scheduler(aiohttp_client: _Client) -> None:
    app = web.Application()
    aiojobs_setup(app)

    app2 = web.Application()
    aiojobs_setup(app2)

    class MyView(web.View):
        async def get(self) -> web.Response:
            assert get_scheduler_from_request(self.request) != get_scheduler_from_app(
                app
            )
            assert get_scheduler_from_request(self.request) == get_scheduler_from_app(
                app2
            )
            return web.Response()

    app2.router.add_route("*", "/", MyView)
    app.add_subapp("/sub/", app2)

    client = await aiohttp_client(app)
    resp = await client.get("/sub/")
    assert resp.status == 200


async def test_nested_application_not_set(aiohttp_client: _Client) -> None:
    app = web.Application()
    app2 = web.Application()

    class MyView(web.View):
        async def get(self) -> web.Response:
            assert get_scheduler_from_request(self.request) is None
            return web.Response()

    app2.router.add_route("*", "/", MyView)
    app.add_subapp("/sub/", app2)

    client = await aiohttp_client(app)
    resp = await client.get("/sub/")
    assert resp.status == 200


@pytest.mark.parametrize(
    "graceful_timeout, result", [(None, False), (2.0, True), (1.0, False)]
)
async def test_graceful_shutdown(
    aiohttp_client: _Client,
    graceful_timeout: float,
    result: bool,
) -> None:
    futs = []

    class MyView(web.View):
        @atomic
        async def get(self) -> web.Response:
            fut = asyncio.Future()
            futs.append(fut)
            await asyncio.sleep(app.sleep)
            fut.set_result(None)
            return web.Response(text=self.request.method)

    async def send_request_with_timeout(timeout: Optional[float] = None):
        try:
            await client.get("/", timeout=ClientTimeout(total=timeout))
        except asyncio.TimeoutError:
            pass

    app = web.Application()
    app.router.add_route("*", "/", MyView)
    aiojobs_setup(app, graceful_timeout=graceful_timeout)

    client = await aiohttp_client(app)

    app.sleep = 3.0
    await send_request_with_timeout(timeout=1.0)

    app.sleep = 0
    await send_request_with_timeout()

    await app.cleanup()

    assert len(futs)
    assert all([fut.done() for fut in futs]) == result
