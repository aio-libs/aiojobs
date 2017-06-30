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
    scheduler = make_scheduler(exception_handler=exc_handler)

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


async def test_exception_non_waited_job(scheduler, loop):
    exc = RuntimeError()

    async def coro():
        await asyncio.sleep(0, loop=loop)
        raise exc

    exc_handler = mock.Mock()
    scheduler.set_exception_handler(exc_handler)
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


def test_close_timeout(scheduler):
    assert scheduler.close_timeout == 0.1
    scheduler.close_timeout = 1
    assert scheduler.close_timeout == 1


async def test_job_repr(scheduler, loop):
    async def coro():
        return

    job = await scheduler.spawn(coro())
    assert repr(job).startswith('<Job')
    assert repr(job).endswith('>')


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


def test_exception_handler_api(scheduler):
    assert scheduler.get_exception_handler() is None
    handler = mock.Mock()
    scheduler.set_exception_handler(handler)
    assert scheduler.get_exception_handler() is handler
    with pytest.raises(TypeError):
        scheduler.set_exception_handler(1)
    scheduler.set_exception_handler(None)
    assert scheduler.get_exception_handler() is None


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
        await job.wait(0.01)
    assert job.closed
    assert len(scheduler) == 0


async def test_timeout_on_closing(scheduler, loop):

    fut1 = create_future(loop)
    fut2 = create_future(loop)

    async def coro():
        try:
            await fut1
        except asyncio.CancelledError:
            await fut2

    exc_handler = mock.Mock()
    scheduler.set_exception_handler(exc_handler)
    scheduler.close_timeout = 0.01
    job = await scheduler.spawn(coro())
    await asyncio.sleep(0.001, loop=loop)
    await job.close()
    assert job.closed
    assert fut1.cancelled()
    expect = {'message': 'Job closing timed out',
              'job': job,
              'exception': mock.ANY}
    if loop.get_debug():
        expect['source_traceback'] = mock.ANY
    exc_handler.assert_called_with(scheduler, expect)


def test_limit(scheduler):
    assert scheduler.limit == 100
    scheduler.limit = 2
    assert scheduler.limit == 2


async def test_scheduler_councurrency_limit(scheduler, loop):
    async def coro(fut):
        await fut

    scheduler.limit = 1
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0

    fut1 = create_future(loop)
    job1 = await scheduler.spawn(coro(fut1))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert 'pending' not in repr(job1)
    assert 'closed' not in repr(job1)

    fut2 = create_future(loop)
    job2 = await scheduler.spawn(coro(fut2))

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 1
    assert 'pending' in repr(job2)
    assert 'closed' not in repr(job2)

    fut1.set_result(None)
    await job1.wait()

    assert scheduler.active_count == 1
    assert scheduler.pending_count == 0
    assert 'pending' not in repr(job1)
    assert 'closed' in repr(job1)
    assert 'pending' not in repr(job2)
    assert 'closed' not in repr(job2)

    fut2.set_result(None)
    await job2.wait()

    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0
    assert 'pending' not in repr(job1)
    assert 'closed' in repr(job1)
    assert 'pending' not in repr(job2)
    assert 'closed' in repr(job2)


async def test_resume_closed_task(scheduler, loop):
    async def coro(fut):
        await fut

    scheduler.limit = 1
    assert scheduler.active_count == 0

    fut1 = create_future(loop)
    job1 = await scheduler.spawn(coro(fut1))

    assert scheduler.active_count == 1

    fut2 = create_future(loop)
    job2 = await scheduler.spawn(coro(fut2))

    assert scheduler.active_count == 1

    await job2.close()
    assert job2.closed
    assert 'closed' in repr(job2)
    assert 'pending' not in repr(job2)

    fut1.set_result(None)
    await job1.wait()

    assert scheduler.active_count == 0
    assert len(scheduler) == 0


async def test_concurreny_disabled(scheduler, loop):
    fut1 = create_future(loop)
    fut2 = create_future(loop)

    async def coro():
        fut1.set_result(None)
        await fut2

    scheduler.limit = None
    job = await scheduler.spawn(coro())
    await fut1
    assert scheduler.active_count == 1

    fut2.set_result(None)
    await job.wait()
    assert scheduler.active_count == 0


async def test_run_after_close(scheduler, loop):
    async def coro():
        pass

    await scheduler.close()

    with pytest.raises(RuntimeError):
        await scheduler.spawn(coro())


async def test_penging_property(scheduler, loop):
    async def coro(fut):
        await fut

    scheduler.limit = 1
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0

    fut1 = create_future(loop)
    job1 = await scheduler.spawn(coro(fut1))

    assert not job1.pending

    fut1 = create_future(loop)
    job1 = await scheduler.spawn(coro(fut1))

    assert job1.pending


async def test_active_property(scheduler, loop):
    async def coro(fut):
        await fut

    scheduler.limit = 1
    assert scheduler.active_count == 0
    assert scheduler.pending_count == 0

    fut1 = create_future(loop)
    job1 = await scheduler.spawn(coro(fut1))

    assert job1.active

    fut1 = create_future(loop)
    job1 = await scheduler.spawn(coro(fut1))

    assert not job1.active


async def test_task_cancelling(loop):
    async def f():
        print('1')
        try:
            print('2')
            await asyncio.sleep(0, loop=loop)
        except asyncio.CancelledError:
            print('Cancelled')

    task = loop.create_task(f())
    await asyncio.sleep(0, loop=loop)
    task.cancel()
    await asyncio.sleep(1, loop=loop)
