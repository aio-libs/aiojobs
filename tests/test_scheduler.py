import asyncio
import sys
from typing import Awaitable, Callable, List, NoReturn
from unittest import mock

import pytest

from aiojobs import Scheduler

if sys.version_info >= (3, 11):
    from asyncio import timeout as asyncio_timeout
else:
    from async_timeout import timeout as asyncio_timeout

_MakeScheduler = Callable[..., Awaitable[Scheduler]]


def test_ctor(scheduler: Scheduler) -> None:
    assert len(scheduler) == 0


async def test_spawn(scheduler: Scheduler) -> None:
    async def coro() -> None:
        await asyncio.sleep(1)

    job = await scheduler.spawn(coro())
    assert not job.closed

    assert len(scheduler) == 1
    assert list(scheduler) == [job]
    assert job in scheduler


async def test_run_retval(scheduler: Scheduler) -> None:
    async def coro() -> int:
        return 1

    job = await scheduler.spawn(coro())
    ret = await job.wait()
    assert ret == 1

    assert job.closed

    assert len(scheduler) == 0
    assert list(scheduler) == []
    assert job not in scheduler


async def test_exception_in_explicit_waiting(make_scheduler: _MakeScheduler) -> None:
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)

    async def coro() -> NoReturn:
        await asyncio.sleep(0)
        raise RuntimeError()

    job = await scheduler.spawn(coro())

    with pytest.raises(RuntimeError):
        await job.wait()

    assert job.closed

    assert len(scheduler) == 0
    assert list(scheduler) == []
    assert job not in scheduler
    assert not exc_handler.called


async def test_exception_non_waited_job(make_scheduler: _MakeScheduler) -> None:
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)
    exc = RuntimeError()

    async def coro() -> NoReturn:
        await asyncio.sleep(0)
        raise exc

    await scheduler.spawn(coro())
    assert len(scheduler) == 1

    await asyncio.sleep(0.05)

    assert len(scheduler) == 0

    expect = {"exception": exc, "job": mock.ANY, "message": "Job processing failed"}
    if asyncio.get_running_loop().get_debug():
        expect["source_traceback"] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_exception_on_close(make_scheduler: _MakeScheduler) -> None:
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)
    exc = RuntimeError()

    fut: asyncio.Future[None] = asyncio.Future()

    async def coro() -> NoReturn:
        fut.set_result(None)
        raise exc

    await scheduler.spawn(coro())
    assert len(scheduler) == 1

    await scheduler.close()

    assert len(scheduler) == 0

    expect = {"exception": exc, "job": mock.ANY, "message": "Job processing failed"}
    if asyncio.get_running_loop().get_debug():
        expect["source_traceback"] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_close_timeout(make_scheduler: _MakeScheduler) -> None:
    s1 = await make_scheduler()
    assert s1.close_timeout == 0.1
    s2 = await make_scheduler(close_timeout=1)
    assert s2.close_timeout == 1


async def test_scheduler_repr(scheduler: Scheduler) -> None:
    async def coro() -> None:
        await asyncio.sleep(1)

    assert repr(scheduler) == "<Scheduler jobs=0>"

    await scheduler.spawn(coro())
    assert repr(scheduler) == "<Scheduler jobs=1>"

    await scheduler.close()
    assert repr(scheduler) == "<Scheduler closed jobs=0>"


async def test_close_jobs(scheduler: Scheduler) -> None:
    async def coro() -> None:
        await asyncio.sleep(1)

    assert not scheduler.closed

    job = await scheduler.spawn(coro())
    await scheduler.close()
    assert job.closed
    assert scheduler.closed
    assert len(scheduler) == 0  # type: ignore[unreachable]
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0


async def test_exception_handler_api(make_scheduler: _MakeScheduler) -> None:
    s1 = await make_scheduler()
    assert s1.exception_handler is None

    handler = mock.Mock()
    s2 = await make_scheduler(exception_handler=handler)
    assert s2.exception_handler is handler

    with pytest.raises(TypeError):
        await make_scheduler(exception_handler=1)

    s3 = await make_scheduler(exception_handler=None)
    assert s3.exception_handler is None


async def test_exception_handler_default(scheduler: Scheduler) -> None:
    handler = mock.Mock()
    event_loop = asyncio.get_running_loop()
    event_loop.set_exception_handler(handler)
    d = {"a": "b"}
    scheduler.call_exception_handler(d)
    handler.assert_called_with(event_loop, d)


async def test_wait_with_timeout(scheduler: Scheduler) -> None:
    async def coro() -> None:
        await asyncio.sleep(1)

    job = await scheduler.spawn(coro())
    with pytest.raises(asyncio.TimeoutError):
        await job.wait(timeout=0.01)
    assert job.closed
    assert len(scheduler) == 0


async def test_timeout_on_closing(make_scheduler: _MakeScheduler) -> None:
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler, close_timeout=0.01)
    fut1: asyncio.Future[None] = asyncio.Future()
    fut2: asyncio.Future[None] = asyncio.Future()

    async def coro() -> None:
        try:
            await fut1
        except asyncio.CancelledError:
            await fut2

    job = await scheduler.spawn(coro())
    await asyncio.sleep(0.001)
    await scheduler.close()
    assert job.closed
    assert fut1.cancelled()
    expect = {"message": "Job closing timed out", "job": job, "exception": mock.ANY}
    if asyncio.get_running_loop().get_debug():
        expect["source_traceback"] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_exception_on_closing(make_scheduler: _MakeScheduler) -> None:
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)
    fut: asyncio.Future[None] = asyncio.Future()
    exc = RuntimeError()

    async def coro() -> NoReturn:
        fut.set_result(None)
        raise exc

    job = await scheduler.spawn(coro())
    await fut
    await scheduler.close()
    assert job.closed
    expect = {"message": "Job processing failed", "job": job, "exception": exc}
    if asyncio.get_running_loop().get_debug():
        expect["source_traceback"] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_limit(make_scheduler: _MakeScheduler) -> None:
    s1 = await make_scheduler()
    assert s1.limit == 100
    s2 = await make_scheduler(limit=2)
    assert s2.limit == 2


async def test_pending_limit(make_scheduler: _MakeScheduler) -> None:
    s1 = await make_scheduler()
    assert s1.pending_limit == 10000
    s2 = await make_scheduler(pending_limit=2)
    assert s2.pending_limit == 2


async def test_pending_queue_infinite(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)

    async def coro(fut: "asyncio.Future[None]") -> None:
        await fut

    fut1: "asyncio.Future[None]" = asyncio.Future()
    fut2: "asyncio.Future[None]" = asyncio.Future()
    fut3: "asyncio.Future[None]" = asyncio.Future()

    await scheduler.spawn(coro(fut1))
    assert scheduler.pending_count == 0

    await scheduler.spawn(coro(fut2))
    assert scheduler.pending_count == 1

    await scheduler.spawn(coro(fut3))
    assert scheduler.pending_count == 2


async def test_pending_queue_limit_wait(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1, pending_limit=1)

    async def coro(fut: "asyncio.Future[None]") -> None:
        await asyncio.sleep(0)
        await fut

    fut1: "asyncio.Future[None]" = asyncio.Future()
    fut2: "asyncio.Future[None]" = asyncio.Future()
    fut3: "asyncio.Future[None]" = asyncio.Future()

    await scheduler.spawn(coro(fut1))
    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0

    await scheduler.spawn(coro(fut2))
    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1

    with pytest.raises(asyncio.TimeoutError):
        # try to wait for 1 sec to add task to pending queue
        async with asyncio_timeout(1):
            await scheduler.spawn(coro(fut3))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1


async def test_scheduler_concurrency_pending_limit(
    make_scheduler: _MakeScheduler,
) -> None:
    scheduler = await make_scheduler(limit=1, pending_limit=1)

    async def coro(fut: "asyncio.Future[object]") -> None:
        await fut

    futures: List["asyncio.Future[object]"] = [asyncio.Future() for _ in range(3)]
    jobs = []

    async def spawn() -> None:
        for fut in futures:
            jobs.append(await scheduler.spawn(coro(fut)))

    task = asyncio.create_task(spawn())
    await asyncio.sleep(0)

    assert len(scheduler) == 2
    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1

    for fut in futures:
        fut.set_result(None)

    for job in jobs:
        await job.wait()

    await task

    assert len(scheduler) == 0
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert all(job.closed for job in jobs)


async def test_scheduler_concurrency_limit(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)

    async def coro(fut: "asyncio.Future[None]") -> None:
        await fut

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0

    fut1: "asyncio.Future[None]" = asyncio.Future()
    job1 = await scheduler.spawn(coro(fut1))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert job1.active

    fut2: "asyncio.Future[None]" = asyncio.Future()
    job2 = await scheduler.spawn(coro(fut2))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1
    assert job2.pending

    fut1.set_result(None)
    await job1.wait()

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert job1.closed
    assert job2.active

    fut2.set_result(None)
    await job2.wait()

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert job1.closed
    assert job2.closed


async def test_resume_closed_task(make_scheduler: _MakeScheduler) -> None:
    scheduler = await make_scheduler(limit=1)

    async def coro(fut: "asyncio.Future[None]") -> None:
        await fut

    assert scheduler.active_count == 0

    fut1: asyncio.Future[None] = asyncio.Future()
    job1 = await scheduler.spawn(coro(fut1))

    assert scheduler.active_count == 1

    fut2: asyncio.Future[None] = asyncio.Future()
    job2 = await scheduler.spawn(coro(fut2))

    assert scheduler.active_count == 1

    await job2.close()
    assert job2.closed
    assert not job2.pending

    fut1.set_result(None)
    await job1.wait()

    assert scheduler.active_count == 0
    assert len(scheduler) == 0


async def test_concurrency_disabled(make_scheduler: _MakeScheduler) -> None:
    fut1: asyncio.Future[None] = asyncio.Future()
    fut2: asyncio.Future[None] = asyncio.Future()

    scheduler = await make_scheduler(limit=None)

    async def coro() -> None:
        fut1.set_result(None)
        await fut2

    job = await scheduler.spawn(coro())
    await fut1
    assert scheduler.active_count == 1

    fut2.set_result(None)
    await job.wait()
    assert scheduler.active_count == 0


async def test_run_after_close(scheduler: Scheduler) -> None:
    async def f() -> None:
        pass

    await scheduler.close()

    coro = f()
    with pytest.raises(RuntimeError):
        await scheduler.spawn(coro)

    with pytest.warns(RuntimeWarning):
        del coro


async def test_shield(scheduler: Scheduler) -> None:
    async def coro() -> str:
        await asyncio.sleep(0)
        return "TEST"

    result = await scheduler.shield(coro())
    assert result == "TEST"
    assert len(scheduler._shields) == 0


async def test_shielded_task_continues(scheduler: Scheduler) -> None:
    completed = False

    async def inner() -> None:
        nonlocal completed
        await asyncio.sleep(0.1)
        completed = True

    async def outer() -> None:
        await scheduler.shield(inner())

    t = asyncio.create_task(outer())
    await asyncio.sleep(0)
    t.cancel()
    with pytest.raises(asyncio.CancelledError):
        await t

    assert not completed
    assert len(scheduler._shields) == 1
    await asyncio.sleep(0.11)
    assert completed
    assert len(scheduler._shields) == 0  # type: ignore[unreachable]


async def test_wait_and_close(scheduler: Scheduler) -> None:
    inner_done = outer_done = False

    async def inner() -> None:
        nonlocal inner_done
        await asyncio.sleep(0.1)
        inner_done = True

    async def outer() -> None:
        nonlocal outer_done
        await scheduler.shield(inner())
        await asyncio.sleep(0.1)
        outer_done = True

    await scheduler.spawn(outer())
    await asyncio.sleep(0)
    assert not inner_done and not outer_done
    assert len(scheduler._shields) == 1
    assert len(scheduler._jobs) == 1

    await scheduler.wait_and_close()
    assert inner_done and outer_done  # type: ignore[unreachable]
    assert len(scheduler._shields) == 0  # type: ignore[unreachable]
    assert len(scheduler._jobs) == 0
    assert scheduler.closed


async def test_wait_and_close_timeout(scheduler: Scheduler) -> None:
    inner_done = outer_cancelled = False

    async def inner() -> None:
        nonlocal inner_done
        await asyncio.sleep(0.1)
        inner_done = True

    async def outer() -> None:
        nonlocal outer_cancelled
        await scheduler.shield(inner())
        try:
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            outer_cancelled = True

    await scheduler.spawn(outer())
    await asyncio.sleep(0)
    assert not inner_done and not outer_cancelled
    assert len(scheduler._shields) == 1
    assert len(scheduler._jobs) == 1

    await scheduler.wait_and_close(0.2)
    assert inner_done and outer_cancelled  # type: ignore[unreachable]
    assert len(scheduler._shields) == 0  # type: ignore[unreachable]
    assert len(scheduler._jobs) == 0
    assert scheduler.closed


async def test_wait_and_close_timeout_shield() -> None:
    inner_cancelled = outer_cancelled = False

    async def inner() -> None:
        nonlocal inner_cancelled
        try:
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            inner_cancelled = True
            raise

    async def outer() -> None:
        nonlocal outer_cancelled
        try:
            await scheduler.shield(inner())
        except asyncio.CancelledError:
            outer_cancelled = True

    async with Scheduler(wait_timeout=0.1) as scheduler:
        await scheduler.spawn(outer())
        await asyncio.sleep(0)
        assert not inner_cancelled and not outer_cancelled
        assert len(scheduler._shields) == 1
        assert len(scheduler._jobs) == 1

    assert inner_cancelled and outer_cancelled  # type: ignore[unreachable]
    assert len(scheduler._shields) == 0  # type: ignore[unreachable]
    assert len(scheduler._jobs) == 0
    assert scheduler.closed


async def test_wait_and_close_spawn(scheduler: Scheduler) -> None:
    another_spawned = another_done = False

    async def another() -> None:
        nonlocal another_done
        await scheduler.shield(asyncio.sleep(0.1))
        another_done = True

    async def coro() -> None:
        nonlocal another_spawned
        await asyncio.sleep(0.1)
        another_spawned = True
        await scheduler.spawn(another())

    await scheduler.spawn(coro())
    await asyncio.sleep(0)

    assert not another_spawned and not another_done
    await scheduler.wait_and_close()
    assert another_spawned and another_done  # type: ignore[unreachable]


def test_scheduler_must_be_created_within_running_loop() -> None:
    with pytest.raises(RuntimeError) as exc_info:
        Scheduler(close_timeout=0, limit=0, pending_limit=0, exception_handler=None)

    assert exc_info.match("no (current|running) event loop")
