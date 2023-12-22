import asyncio
from contextlib import suppress
from typing import Awaitable, Callable, NoReturn
from unittest import mock

import pytest

from aiojobs._scheduler import Scheduler

_MakeScheduler = Callable[..., Awaitable[Scheduler]]


async def test_job_spawned(scheduler: Scheduler) -> None:
    async def coro() -> None:
        pass

    job = await scheduler.spawn(coro())
    assert job.active
    assert not job.closed
    assert not job.pending
    assert "closed" not in repr(job)
    assert "pending" not in repr(job)

    assert repr(job).startswith("<Job")
    assert repr(job).endswith(">")


async def test_job_awaited(scheduler: Scheduler) -> None:
    async def coro() -> None:
        pass

    job = await scheduler.spawn(coro())
    await job.wait()

    assert not job.active
    assert job.closed
    assert not job.pending
    assert "closed" in repr(job)
    assert "pending" not in repr(job)


async def test_job_closed(scheduler: Scheduler) -> None:
    async def coro() -> None:
        pass

    job = await scheduler.spawn(coro())
    await job.close()

    assert not job.active
    assert job.closed
    assert not job.pending
    assert "closed" in repr(job)
    assert "pending" not in repr(job)


async def test_job_pending(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)

    async def coro1() -> None:
        await asyncio.sleep(10)

    async def coro2() -> None:
        pass

    await scheduler.spawn(coro1())
    job = await scheduler.spawn(coro2())

    assert not job.active
    assert not job.closed
    assert job.pending
    assert "closed" not in repr(job)
    assert "pending" in repr(job)


# Mangle a name for satisfy 'pending' not in repr check
async def test_job_resume_after_p_e_nding(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)

    async def coro1() -> None:
        await asyncio.sleep(10)

    async def coro2() -> None:
        pass

    job1 = await scheduler.spawn(coro1())
    job2 = await scheduler.spawn(coro2())

    await job1.close()

    assert job2.active
    assert not job2.closed
    assert not job2.pending
    assert "closed" not in repr(job2)
    assert "pending" not in repr(job2)


async def test_job_wait_result(make_scheduler: _MakeScheduler) -> None:
    handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=handler)

    async def coro() -> int:
        return 1

    job = await scheduler.spawn(coro())
    ret = await job.wait()
    assert ret == 1
    assert not handler.called


async def test_job_wait_exception(make_scheduler: _MakeScheduler) -> None:
    handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=handler)
    exc = RuntimeError()

    async def coro() -> NoReturn:
        raise exc

    job = await scheduler.spawn(coro())
    with pytest.raises(RuntimeError) as ctx:
        await job.wait()
    assert ctx.value is exc
    assert not handler.called


async def test_job_close_exception(make_scheduler: _MakeScheduler) -> None:
    handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=handler)
    exc = RuntimeError()
    fut: asyncio.Future[None] = asyncio.Future()

    async def coro() -> NoReturn:
        fut.set_result(None)
        raise exc

    job = await scheduler.spawn(coro())
    await fut

    with pytest.raises(RuntimeError):
        await job.close()
    assert not handler.called


async def test_job_close_timeout(make_scheduler: _MakeScheduler) -> None:
    handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=handler, close_timeout=0.01)

    fut1: asyncio.Future[None] = asyncio.Future()
    fut2: asyncio.Future[None] = asyncio.Future()

    async def coro() -> None:
        fut1.set_result(None)
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            await fut2

    job = await scheduler.spawn(coro())
    await fut1

    with pytest.raises(asyncio.TimeoutError):
        await job.close()
    assert not handler.called


async def test_job_await_pending(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)

    fut: asyncio.Future[None] = asyncio.Future()

    async def coro1() -> None:
        await fut

    async def coro2() -> int:
        return 1

    await scheduler.spawn(coro1())
    job = await scheduler.spawn(coro2())

    asyncio.get_running_loop().call_later(0.01, fut.set_result, None)
    ret = await job.wait()
    assert ret == 1


async def test_job_cancel_awaiting(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler()

    fut = asyncio.get_running_loop().create_future()

    async def f() -> None:
        await fut

    job = await scheduler.spawn(f())

    task = asyncio.create_task(job.wait())
    assert job.active, job
    await asyncio.sleep(0.05)
    assert job.active, job
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task

    assert not fut.cancelled()
    fut.set_result(None)


async def test_job_wait_closed(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)
    fut: asyncio.Future[None] = asyncio.Future()

    async def coro1() -> NoReturn:
        raise RuntimeError()

    async def coro2() -> None:
        fut.set_result(None)

    job = await scheduler.spawn(coro1())
    await scheduler.spawn(coro2())

    await fut
    with pytest.raises(RuntimeError):
        await job.wait()


async def test_job_close_closed(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)
    fut: asyncio.Future[None] = asyncio.Future()

    async def coro1() -> NoReturn:
        raise RuntimeError()

    async def coro2() -> None:
        fut.set_result(None)

    job = await scheduler.spawn(coro1())
    await scheduler.spawn(coro2())

    await fut
    await job.close()


async def test_job_await_closed(scheduler: Scheduler) -> None:
    async def coro() -> int:
        return 5

    job = await scheduler.spawn(coro())
    assert not job._closed

    # Let coro run.
    await asyncio.sleep(0)
    # Then let done callback run.
    await asyncio.sleep(0)

    assert job._closed
    # https://github.com/python/mypy/issues/11853
    assert job._task.done()  # type: ignore[unreachable]
    assert await job.wait() == 5


async def test_job_await_explicit_close(scheduler: Scheduler) -> None:
    async def coro() -> None:
        await asyncio.sleep(1)

    job = await scheduler.spawn(coro())
    assert not job._closed

    # Ensure coro() task is started before close().
    await asyncio.sleep(0)
    await job.close()

    assert job._closed
    assert job._task.done()  # type: ignore[unreachable]
    with pytest.raises(asyncio.CancelledError):
        await job.wait()


async def test_exception_handler_called_once(make_scheduler: _MakeScheduler) -> None:
    handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=handler)

    async def coro() -> NoReturn:
        raise Exception()

    await scheduler.spawn(coro())
    await scheduler.close()
    handler.assert_called_once()


async def test_get_job_name(scheduler: Scheduler) -> None:
    async def coro() -> None:
        """Dummy function."""

    job = await scheduler.spawn(coro(), name="test_job_name")
    assert job.get_name() == "test_job_name"
    assert job._task is not None
    assert job._task.get_name() == "test_job_name"


async def test_get_default_job_name(scheduler: Scheduler) -> None:
    async def coro() -> None:
        """Dummy function."""

    job = await scheduler.spawn(coro())
    job_name = job.get_name()
    assert job_name is not None
    assert job_name.startswith("Task-")


async def test_set_job_name(scheduler: Scheduler) -> None:
    async def coro() -> None:
        """Dummy function."""

    job = await scheduler.spawn(coro(), name="original_name")
    job.set_name("changed_name")
    assert job.get_name() == "changed_name"
    assert job._task is not None
    assert job._task.get_name() == "changed_name"
