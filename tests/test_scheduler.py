import asyncio
from unittest import mock

import pytest


def test_ctor(scheduler):
    assert len(scheduler) == 0


async def test_spawn(scheduler, loop):
    async def coro():
        await asyncio.sleep(1, loop=loop)
    job = await scheduler.spawn(coro())
    assert not job.closed

    assert len(scheduler) == 1
    assert list(scheduler) == [job]
    assert job in scheduler


async def test_run_retval(scheduler, loop):
    async def coro():
        return 1
    job = await scheduler.spawn(coro())
    ret = await job.wait()
    assert ret == 1

    assert job.closed

    assert len(scheduler) == 0
    assert list(scheduler) == []
    assert job not in scheduler


async def test_exception_in_explicit_waiting(make_scheduler, loop):
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)

    async def coro():
        await asyncio.sleep(0, loop=loop)
        raise RuntimeError()

    job = await scheduler.spawn(coro())

    with pytest.raises(RuntimeError):
        await job.wait()

    assert job.closed

    assert len(scheduler) == 0
    assert list(scheduler) == []
    assert job not in scheduler
    assert not exc_handler.called


async def test_exception_non_waited_job(make_scheduler, loop):
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)
    exc = RuntimeError()

    async def coro():
        await asyncio.sleep(0, loop=loop)
        raise exc

    await scheduler.spawn(coro())
    assert len(scheduler) == 1

    await asyncio.sleep(0.05, loop=loop)

    assert len(scheduler) == 0

    expect = {'exception': exc,
              'job': mock.ANY,
              'message': 'Job processing failed'}
    if loop.get_debug():
        expect['source_traceback'] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_exception_on_close(make_scheduler, loop):
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)
    exc = RuntimeError()

    fut = asyncio.Future()

    async def coro():
        fut.set_result(None)
        raise exc

    await scheduler.spawn(coro())
    assert len(scheduler) == 1

    await scheduler.close()

    assert len(scheduler) == 0

    expect = {'exception': exc,
              'job': mock.ANY,
              'message': 'Job processing failed'}
    if loop.get_debug():
        expect['source_traceback'] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_close_timeout(make_scheduler):
    s1 = await make_scheduler()
    assert s1.close_timeout == 0.1
    s2 = await make_scheduler(close_timeout=1)
    assert s2.close_timeout == 1


async def test_scheduler_repr(scheduler, loop):
    async def coro():
        await asyncio.sleep(1, loop=loop)

    assert repr(scheduler) == '<Scheduler jobs=0>'

    await scheduler.spawn(coro())
    assert repr(scheduler) == '<Scheduler jobs=1>'

    await scheduler.close()
    assert repr(scheduler) == '<Scheduler closed jobs=0>'


async def test_close_jobs(scheduler, loop):
    async def coro():
        await asyncio.sleep(1, loop=loop)

    assert not scheduler.closed

    job = await scheduler.spawn(coro())
    await scheduler.close()
    assert job.closed
    assert scheduler.closed
    assert len(scheduler) == 0
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0


async def test_exception_handler_api(make_scheduler):
    s1 = await make_scheduler()
    assert s1.exception_handler is None

    handler = mock.Mock()
    s2 = await make_scheduler(exception_handler=handler)
    assert s2.exception_handler is handler

    with pytest.raises(TypeError):
        await make_scheduler(exception_handler=1)

    s3 = await make_scheduler(exception_handler=None)
    assert s3.exception_handler is None


def test_exception_handler_default(scheduler, loop):
    handler = mock.Mock()
    loop.set_exception_handler(handler)
    d = {'a': 'b'}
    scheduler.call_exception_handler(d)
    handler.assert_called_with(loop, d)


async def test_wait_with_timeout(scheduler, loop):
    async def coro():
        await asyncio.sleep(1, loop=loop)

    job = await scheduler.spawn(coro())
    with pytest.raises(asyncio.TimeoutError):
        await job.wait(timeout=0.01)
    assert job.closed
    assert len(scheduler) == 0


async def test_timeout_on_closing(make_scheduler, loop):
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler,
                                     close_timeout=0.01)
    fut1 = asyncio.Future()
    fut2 = asyncio.Future()

    async def coro():
        try:
            await fut1
        except asyncio.CancelledError:
            await fut2

    job = await scheduler.spawn(coro())
    await asyncio.sleep(0.001, loop=loop)
    await scheduler.close()
    assert job.closed
    assert fut1.cancelled()
    expect = {'message': 'Job closing timed out',
              'job': job,
              'exception': mock.ANY}
    if loop.get_debug():
        expect['source_traceback'] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_exception_on_closing(make_scheduler, loop):
    exc_handler = mock.Mock()
    scheduler = await make_scheduler(exception_handler=exc_handler)
    fut = asyncio.Future()
    exc = RuntimeError()

    async def coro():
        fut.set_result(None)
        raise exc

    job = await scheduler.spawn(coro())
    await fut
    await scheduler.close()
    assert job.closed
    expect = {'message': 'Job processing failed',
              'job': job,
              'exception': exc}
    if loop.get_debug():
        expect['source_traceback'] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


async def test_limit(make_scheduler):
    s1 = await make_scheduler()
    assert s1.limit == 100
    s2 = await make_scheduler(limit=2)
    assert s2.limit == 2


async def test_scheduler_concurrency_limit(make_scheduler):
    scheduler = await make_scheduler(limit=1)

    async def coro(fut):
        await fut

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0

    fut1 = asyncio.Future()
    job1 = await scheduler.spawn(coro(fut1))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert job1.active

    fut2 = asyncio.Future()
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


async def test_resume_closed_task(make_scheduler):
    scheduler = await make_scheduler(limit=1)

    async def coro(fut):
        await fut

    assert scheduler.active_count == 0

    fut1 = asyncio.Future()
    job1 = await scheduler.spawn(coro(fut1))

    assert scheduler.active_count == 1

    fut2 = asyncio.Future()
    job2 = await scheduler.spawn(coro(fut2))

    assert scheduler.active_count == 1

    await job2.close()
    assert job2.closed
    assert not job2.pending

    fut1.set_result(None)
    await job1.wait()

    assert scheduler.active_count == 0
    assert len(scheduler) == 0


async def test_concurrency_disabled(make_scheduler):
    fut1 = asyncio.Future()
    fut2 = asyncio.Future()

    scheduler = await make_scheduler(limit=None)

    async def coro():
        fut1.set_result(None)
        await fut2

    job = await scheduler.spawn(coro())
    await fut1
    assert scheduler.active_count == 1

    fut2.set_result(None)
    await job.wait()
    assert scheduler.active_count == 0


async def test_pending_limit(make_scheduler):
    s1 = await make_scheduler()
    assert s1.pending_limit == 100
    s2 = await make_scheduler(pending_limit=2)
    assert s2.pending_limit == 2


async def test_scheduler_pending_limit(make_scheduler, loop):
    scheduler = await make_scheduler(limit=1, pending_limit=1)

    async def coro1(fut):
        await fut

    async def coro2():
        return 1

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0

    fut1 = asyncio.Future()
    fut2 = asyncio.Future()
    job1 = await scheduler.spawn(coro1(fut1))
    job2 = await scheduler.spawn(coro1(fut2))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1
    assert scheduler.waiting_count == 0
    assert job2.pending

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(scheduler.spawn(coro2),
                               timeout=0.01,
                               loop=loop)
    await asyncio.sleep(0.01, loop=loop)

    assert scheduler.waiting_count == 0

    fut3 = asyncio.Future()
    job3_fut = asyncio.ensure_future(scheduler.spawn(coro1(fut3)), loop=loop)
    await asyncio.sleep(0.01, loop=loop)

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1
    assert scheduler.waiting_count == 1
    assert not job3_fut.done()

    fut1.set_result(None)
    await job1.wait()
    job3 = await job3_fut

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1
    assert scheduler.waiting_count == 0
    assert job1.closed
    assert job2.active
    assert job3.pending

    fut2.set_result(None)
    fut3.set_result(None)
    await job2.wait()
    await job3.wait()

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0
    assert job1.closed
    assert job2.closed
    assert job3.closed


async def test_scheduler_pending_disable(make_scheduler, loop):
    scheduler = await make_scheduler(limit=1, pending_limit=0)

    async def coro1(fut):
        await fut

    async def coro2():
        return 1

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0

    fut1 = asyncio.Future()
    job1 = await scheduler.spawn(coro1(fut1))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0
    assert job1.active

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(scheduler.spawn(coro2),
                               timeout=0.01,
                               loop=loop)
    await asyncio.sleep(0.01, loop=loop)

    assert scheduler.waiting_count == 0

    fut2 = asyncio.Future()
    job2_fut = asyncio.ensure_future(scheduler.spawn(coro1(fut2)), loop=loop)
    await asyncio.sleep(0.01, loop=loop)

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 1
    assert not job2_fut.done()

    fut1.set_result(None)
    await job1.wait()
    job2 = await job2_fut

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0
    assert job1.closed
    assert job2.active


async def test_cancel_waiting_task(make_scheduler, loop):
    scheduler = await make_scheduler(limit=1, pending_limit=0)

    async def coro1(fut):
        await fut

    async def coro2():
        return 1

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0

    fut1 = asyncio.Future()
    job1 = await scheduler.spawn(coro1(fut1))
    job2_fut = asyncio.ensure_future(scheduler.spawn(coro2()), loop=loop)
    await asyncio.sleep(0.01, loop=loop)

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 1
    assert job1.active
    assert not job2_fut.done()

    job2_fut.cancel()
    await asyncio.sleep(0.01, loop=loop)

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0
    assert job1.active
    assert job2_fut.cancelled()


async def test_lack_waiting_task(make_scheduler, loop):
    scheduler = await make_scheduler(limit=0, pending_limit=2)

    async def coro1():
        return 1

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert scheduler.waiting_count == 0

    job1 = await scheduler.spawn(coro1())
    job2 = await scheduler.spawn(coro1())

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 2
    assert scheduler.waiting_count == 0
    assert job1.pending
    assert job2.pending

    job3_fut = asyncio.ensure_future(scheduler.spawn(coro1()), loop=loop)
    await job1.close()
    await job2.close()
    job3 = await job3_fut

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 1
    assert scheduler.waiting_count == 0
    assert job1.closed
    assert job2.closed
    assert job3.pending


async def test_run_after_close(scheduler, loop):
    async def f():
        pass

    await scheduler.close()

    coro = f()
    with pytest.raises(RuntimeError):
        await scheduler.spawn(coro)

    with pytest.warns(RuntimeWarning):
        del coro
