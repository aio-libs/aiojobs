import pytest

from aiojobs._scheduler import Scheduler


PARAMS = dict(close_timeout=1.0, limit=100, exception_handler=None)


@pytest.fixture
def scheduler(loop):
    ret = Scheduler(loop=loop, **PARAMS)
    yield ret
    loop.run_until_complete(ret.close())


@pytest.fixture
def make_scheduler(loop):
    schedulers = []

    def maker(**kwargs):
        params = PARAMS.copy()
        params.update(kwargs)
        ret = Scheduler(loop=loop, **params)
        schedulers.append(ret)
        return ret

    yield maker

    for scheduler in schedulers:
        loop.run_until_complete(scheduler.close())
