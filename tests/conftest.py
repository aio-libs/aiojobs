import asyncio
from typing import Any, AsyncIterator, Awaitable, Callable, Dict

import pytest

from aiojobs import create_scheduler
from aiojobs._scheduler import Scheduler

PARAMS: Dict[str, Any] = dict(close_timeout=1.0, limit=100, pending_limit=0, exception_handler=None)


@pytest.fixture
async def scheduler() -> AsyncIterator[Scheduler]:
    scheduler = Scheduler(**PARAMS)
    yield scheduler
    await scheduler.close()


@pytest.fixture
async def make_scheduler() -> AsyncIterator[Callable[..., Awaitable[Scheduler]]]:
    schedulers = []

    async def maker(**kwargs: Any) -> Scheduler:
        ret = await create_scheduler(**kwargs)
        schedulers.append(ret)
        return ret

    yield maker

    await asyncio.gather(*(s.close() for s in schedulers))
