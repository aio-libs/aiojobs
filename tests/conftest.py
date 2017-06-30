import pytest

from aiojobs._scheduler import _Scheduler


PARAMS = dict(close_timeout=1.0, concurrency=100, exception_handler=None)


@pytest.fixture
def scheduler(loop):
    ret = _Scheduler(loop=loop, **PARAMS)
    yield ret
    loop.run_until_complete(ret.close())


@pytest.fixture
def make_scheduler(loop):
    schedulers = []

    def maker(**kwargs):
        params = PARAMS.copy()
        params.update(kwargs)
        ret = _Scheduler(loop=loop, **params)
        schedulers.append(ret)
        return ret

    yield maker

    for scheduler in schedulers:
        loop.run_until_complete(scheduler.close())
