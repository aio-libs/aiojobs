import asyncio
from typing import (
    Any,
    Callable,
    Collection,
    Coroutine,
    Dict,
    Iterator,
    Optional,
    Set,
    TypeVar,
)

from ._job import Job

_T = TypeVar("_T")
ExceptionHandler = Callable[["Scheduler", Dict[str, Any]], None]


class Scheduler(Collection[Job[object]]):
    def __init__(
        self,
        *,
        close_timeout: Optional[float] = 0.1,
        limit: Optional[int] = 100,
        pending_limit: int = 10000,
        exception_handler: Optional[ExceptionHandler] = None,
    ):
        if exception_handler is not None and not callable(exception_handler):
            raise TypeError(
                "A callable object or None is expected, "
                "got {!r}".format(exception_handler)
            )

        self._jobs: Set[Job[object]] = set()
        self._close_timeout = close_timeout
        self._limit = limit
        self._exception_handler = exception_handler
        self._failed_tasks: asyncio.Queue[
            Optional[asyncio.Task[object]]
        ] = asyncio.Queue()
        self._failed_task = asyncio.create_task(self._wait_failed())
        self._pending: asyncio.Queue[Job[object]] = asyncio.Queue(maxsize=pending_limit)
        self._closed = False

    def __iter__(self) -> Iterator[Job[Any]]:
        return iter(self._jobs)

    def __len__(self) -> int:
        return len(self._jobs)

    def __contains__(self, obj: object) -> bool:
        return obj in self._jobs

    def __repr__(self) -> str:
        info = []
        if self._closed:
            info.append("closed")
        state = " ".join(info)
        if state:
            state += " "
        return f"<Scheduler {state}jobs={len(self)}>"

    @property
    def limit(self) -> Optional[int]:
        return self._limit

    @property
    def pending_limit(self) -> int:
        return self._pending.maxsize

    @property
    def close_timeout(self) -> Optional[float]:
        return self._close_timeout

    @property
    def active_count(self) -> int:
        return len(self._jobs) - self._pending.qsize()

    @property
    def pending_count(self) -> int:
        return self._pending.qsize()

    @property
    def closed(self) -> bool:
        return self._closed

    async def spawn(self, coro: Coroutine[object, object, _T]) -> Job[_T]:
        if self._closed:
            raise RuntimeError("Scheduling a new job after closing")
        job = Job(coro, self)
        should_start = self._limit is None or self.active_count < self._limit
        if should_start:
            job._start()
        else:
            try:
                # wait for free slot in queue
                await self._pending.put(job)
            except asyncio.CancelledError:
                await job.close()
                raise
        self._jobs.add(job)
        return job

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True  # prevent adding new jobs

        jobs = self._jobs
        if jobs:
            # cleanup pending queue
            # all job will be started on closing
            while not self._pending.empty():
                self._pending.get_nowait()
            await asyncio.gather(
                *[job._close(self._close_timeout) for job in jobs],
                return_exceptions=True,
            )
            self._jobs.clear()
        self._failed_tasks.put_nowait(None)
        await self._failed_task

    def call_exception_handler(self, context: Dict[str, Any]) -> None:
        handler = self._exception_handler
        if handler is None:
            handler = asyncio.get_running_loop().call_exception_handler(context)
        else:
            handler(self, context)

    @property
    def exception_handler(self) -> Optional[ExceptionHandler]:
        return self._exception_handler

    def _done(self, job: Job[object]) -> None:
        self._jobs.discard(job)
        if not self.pending_count:
            return
        # No pending jobs when limit is None
        # Safe to subtract.
        ntodo = self._limit - self.active_count  # type: ignore[operator]
        i = 0
        while i < ntodo:
            if not self.pending_count:
                return
            new_job = self._pending.get_nowait()
            if new_job.closed:
                continue
            new_job._start()
            i += 1

    async def _wait_failed(self) -> None:
        # a coroutine for waiting failed tasks
        # without awaiting for failed tasks async raises a warning
        while True:
            task = await self._failed_tasks.get()
            if task is None:
                return  # closing
            try:
                await task  # should raise exception
            except Exception:
                # Cleanup a warning
                # self.call_exception_handler() is already called
                # by Job._add_done_callback
                # Thus we caught an task exception and we are good citizens
                pass
