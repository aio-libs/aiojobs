import asyncio
import contextvars
import gc
import inspect
import sys
import warnings
from collections.abc import Awaitable, Coroutine
from typing import Any, Callable
from unittest import mock

import pytest

from aiojobs import Scheduler

_MakeScheduler = Callable[..., Awaitable[Scheduler]]


async def test__immediate_job__keeps_spawn_context_after_await(
    scheduler: Scheduler,
) -> None:
    value = contextvars.ContextVar("value", default="unset")

    async def work() -> tuple[str, str]:
        before = value.get()
        await asyncio.sleep(0)
        return before, value.get()

    value.set("submitted")
    job = await scheduler.spawn(work())
    value.set("caller")
    assert await job.wait() == ("submitted", "submitted")
    assert value.get() == "caller"


async def test__queued_job__keeps_its_own_spawn_context(
    make_scheduler: _MakeScheduler,
) -> None:
    scheduler = await make_scheduler(limit=1)
    value = contextvars.ContextVar("value", default="unset")
    release = asyncio.Event()

    async def blocker() -> None:
        await release.wait()

    async def work() -> tuple[str, str]:
        before = value.get()
        await asyncio.sleep(0)
        return before, value.get()

    value.set("first")
    first = await scheduler.spawn(blocker())
    value.set("queued")
    second = await scheduler.spawn(work())
    value.set("releaser")
    release.set()
    await first.wait()
    assert await second.wait() == ("queued", "queued")
    assert value.get() == "releaser"


async def test__blocked_spawn__captures_context_before_queue_wait(
    make_scheduler: _MakeScheduler,
) -> None:
    scheduler = await make_scheduler(limit=1, pending_limit=1)
    value = contextvars.ContextVar("value", default="unset")
    release = asyncio.Event()

    async def blocker() -> None:
        await release.wait()

    async def work() -> str:
        return value.get()

    first = await scheduler.spawn(blocker())
    queued = await scheduler.spawn(work())
    value.set("before-wait")
    submitter = asyncio.create_task(scheduler.spawn(work()))
    await asyncio.sleep(0)
    assert not submitter.done()
    value.set("other")
    release.set()
    await first.wait()
    assert await queued.wait() == "unset"
    third = await submitter
    assert await third.wait() == "before-wait"


async def test__cancelled_blocked_spawn__closes_its_coroutine(
    make_scheduler: _MakeScheduler,
) -> None:
    scheduler = await make_scheduler(limit=1, pending_limit=1)
    release = asyncio.Event()
    executed = []

    async def blocker() -> None:
        await release.wait()

    async def work() -> None:
        executed.append(True)

    first = await scheduler.spawn(blocker())
    queued = await scheduler.spawn(blocker())
    coro = work()
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", RuntimeWarning)
        submitter = asyncio.create_task(scheduler.spawn(coro))
        await asyncio.sleep(0)
        assert not submitter.done()
        submitter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await submitter
        assert inspect.getcoroutinestate(coro) == inspect.CORO_CLOSED
        await queued.close()
        release.set()
        await first.wait()
        gc.collect()
    assert not executed
    assert not [w for w in recorded if "was never awaited" in str(w.message)]


async def test__running_close__executes_finally(scheduler: Scheduler) -> None:
    started = asyncio.Event()
    finished = asyncio.Event()

    async def work() -> None:
        try:
            started.set()
            await asyncio.sleep(60)
        finally:
            finished.set()

    job = await scheduler.spawn(work())
    await started.wait()
    await job.close()
    assert finished.is_set()


async def test__pending_close__does_not_run_body_or_leave_unawaited_warning(
    make_scheduler: _MakeScheduler,
) -> None:
    scheduler = await make_scheduler(limit=1)
    release = asyncio.Event()
    executed = []

    async def blocker() -> None:
        await release.wait()

    async def work() -> None:
        executed.append(True)

    first = await scheduler.spawn(blocker())
    job = await scheduler.spawn(work())
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", RuntimeWarning)
        await job.close()
        assert inspect.getcoroutinestate(job._coro) == inspect.CORO_CLOSED
        gc.collect()
        release.set()
        await first.wait()
        await scheduler.close()
        gc.collect()
    assert not executed
    assert not [w for w in recorded if "was never awaited" in str(w.message)]


async def test__scheduler_close__closes_pending_coroutine_without_running_it(
    make_scheduler: _MakeScheduler,
) -> None:
    scheduler = await make_scheduler(limit=1, pending_limit=1)
    executed = []

    async def blocker() -> None:
        await asyncio.sleep(60)

    async def work() -> None:
        executed.append(True)

    await scheduler.spawn(blocker())
    coro = work()
    await scheduler.spawn(coro)
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", RuntimeWarning)
        await scheduler.close()
        await scheduler.close()
        gc.collect()
    assert inspect.getcoroutinestate(coro) == inspect.CORO_CLOSED
    assert not executed
    assert not [w for w in recorded if "was never awaited" in str(w.message)]


async def test__active_before_first_step__closes_original_coroutine(
    scheduler: Scheduler,
) -> None:
    executed = []

    async def work() -> None:
        executed.append(True)

    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", RuntimeWarning)
        job = await scheduler.spawn(work())
        await job.close()
        assert inspect.getcoroutinestate(job._coro) == inspect.CORO_CLOSED
        gc.collect()
    assert not executed
    assert not [w for w in recorded if "was never awaited" in str(w.message)]


@pytest.mark.skipif(
    sys.version_info < (3, 11), reason="create_task(context=...) requires Python 3.11"
)
async def test__default_factory__receives_captured_context_without_copy(
    scheduler: Scheduler,
) -> None:
    loop = asyncio.get_running_loop()
    assert loop.get_task_factory() is None

    async def work() -> None:
        await asyncio.sleep(0)

    coro = work()
    with mock.patch.object(loop, "create_task", wraps=loop.create_task) as create_task:
        with mock.patch(
            "aiojobs._job.asyncio.create_task", wraps=asyncio.create_task
        ) as module_create_task:
            job = await scheduler.spawn(coro)
        calls = [call for call in create_task.call_args_list if call.args[0] is coro]
        assert len(calls) == 1
        assert calls[0].kwargs.get("context") is job._context
        assert not [
            call for call in module_create_task.call_args_list if call.args[0] is coro
        ]
    await job.wait()


async def test__legacy_factory__does_not_require_context_keyword(
    scheduler: Scheduler,
) -> None:
    loop = asyncio.get_running_loop()
    original = loop.get_task_factory()
    value = contextvars.ContextVar("value", default="unset")
    seen: list[str] = []

    def factory(
        loop: asyncio.AbstractEventLoop,
        coro: Coroutine[Any, Any, Any],
        *,
        name: str | None = None,
    ) -> asyncio.Task[Any]:
        if coro is job_coro:
            seen.append(value.get())
        return asyncio.Task(coro, loop=loop, name=name)

    async def work() -> str:
        return value.get()

    job_coro = work()
    loop.set_task_factory(factory)  # type: ignore[arg-type]
    try:
        value.set("submission")
        with mock.patch(
            "aiojobs._job.asyncio.create_task", wraps=asyncio.create_task
        ) as module_create_task:
            job = await scheduler.spawn(job_coro, name="legacy-job")
        value.set("caller")
        assert await job.wait() == "submission"
        assert job.get_name() == "legacy-job"
        assert seen == ["submission"]
        assert not [
            call
            for call in module_create_task.call_args_list
            if call.args[0] is job_coro
        ]
    finally:
        loop.set_task_factory(original)


async def test__custom_factory__creates_one_job_task_with_spawn_context(
    scheduler: Scheduler,
) -> None:
    loop = asyncio.get_running_loop()
    original = loop.get_task_factory()
    value = contextvars.ContextVar("value", default="unset")
    created = []

    def factory(
        loop: asyncio.AbstractEventLoop,
        coro: Coroutine[Any, Any, Any],
        **kwargs: Any,
    ) -> asyncio.Task[Any]:
        task = asyncio.Task(coro, loop=loop, **kwargs)
        created.append((task, value.get()))
        return task

    async def work() -> str:
        return value.get()

    loop.set_task_factory(factory)  # type: ignore[arg-type]
    try:
        value.set("spawn")
        job = await scheduler.spawn(work())
        value.set("caller")
        assert await job.wait() == "spawn"
        assert [context for task, context in created if task is job._task] == ["spawn"]
        assert sum(task is job._task for task, _ in created) == 1
    finally:
        loop.set_task_factory(original)


async def test__failed_job_callback__keeps_start_context(
    make_scheduler: _MakeScheduler,
) -> None:
    value = contextvars.ContextVar("value", default="unset")
    seen = []

    def handler(scheduler: Scheduler, context: object) -> None:
        seen.append(value.get())

    scheduler = await make_scheduler(limit=1, exception_handler=handler)
    release = asyncio.Event()

    async def blocker() -> None:
        await release.wait()

    async def broken() -> None:
        raise RuntimeError("broken")

    first = await scheduler.spawn(blocker())
    value.set("submission")
    await scheduler.spawn(broken())
    value.set("completion")
    release.set()
    await first.wait()
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert seen == ["unset"]


@pytest.mark.skipif(
    sys.version_info < (3, 12), reason="eager_task_factory requires Python 3.12"
)
async def test__eager_factory__runs_immediate_job_in_spawn_context(
    scheduler: Scheduler,
) -> None:
    loop = asyncio.get_running_loop()
    original = loop.get_task_factory()
    value = contextvars.ContextVar("value", default="unset")

    async def work() -> str:
        return value.get()

    loop.set_task_factory(asyncio.eager_task_factory)  # type: ignore[attr-defined]
    try:
        value.set("spawn")
        job = await scheduler.spawn(work())
        value.set("caller")
        assert await job.wait() == "spawn"
    finally:
        loop.set_task_factory(original)
