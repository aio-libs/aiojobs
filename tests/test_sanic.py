# -*- coding: utf-8 -*-
import asyncio

import pytest
from sanic import Sanic, response

from aiojobs.sanic import setup as aiojobs_setup
from aiojobs.sanic import spawn


async def test_plugin(test_client):
    job = None

    async def coro():
        await asyncio.sleep(10)

    async def handler(request):
        nonlocal job

        job = await spawn(request, coro())
        assert not job.closed
        return response.text()

    app = Sanic(__name__)
    app.add_route('/', handler)
    aiojobs_setup(app)

    client = await test_client(app)
    resp = await client.get('/')
    assert resp.status == 200

    assert job.active
    await client.close()
    assert job.closed
