import asyncio

import pytest

from aiojobs import create_scheduler
from aiojobs._scheduler import Scheduler

PARAMS = dict(close_timeout=1.0, limit=100, pending_limit=0, exception_handler=None)


@pytest.fixture
async def scheduler():
    async def maker():
        return Scheduler(**PARAMS)

    ret = await maker()
    yield ret
    await ret.close()


@pytest.fixture
async def make_scheduler():
    schedulers = []

    async def maker(**kwargs):
        ret = await create_scheduler(**kwargs)
        schedulers.append(ret)
        return ret

    yield maker

    await asyncio.gather(*(s.close() for s in schedulers))
