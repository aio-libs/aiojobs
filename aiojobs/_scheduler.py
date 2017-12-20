import asyncio
from collections import deque

from ._job import Job

try:
    from collections.abc import Collection
except ImportError:  # pragma: no cover
    # Python 3.5 has no Collection ABC class
    from collections.abc import Sized, Iterable, Container
    bases = Sized, Iterable, Container
else:  # pragma: no cover
    bases = (Collection,)


class Scheduler(*bases):
    def __init__(self, *, close_timeout, limit,
                 exception_handler, loop):
        self._loop = loop
        self._jobs = set()
        self._close_timeout = close_timeout
        self._limit = limit
        self._exception_handler = exception_handler
        self._failed_tasks = asyncio.Queue(loop=loop)
        self._failed_task = loop.create_task(self._wait_failed())
        self._pending = deque()
        self._closed = False

    def __iter__(self):
        return iter(list(self._jobs))

    def __len__(self):
        return len(self._jobs)

    def __contains__(self, job):
        return job in self._jobs

    def __repr__(self):
        info = []
        if self._closed:
            info.append('closed')
        info = ' '.join(info)
        if info:
            info += ' '
        return '<Scheduler {}jobs={}>'.format(info, len(self))

    @property
    def limit(self):
        return self._limit

    @property
    def close_timeout(self):
        return self._close_timeout

    @property
    def active_count(self):
        return len(self._jobs) - len(self._pending)

    @property
    def pending_count(self):
        return len(self._pending)

    @property
    def closed(self):
        return self._closed

    async def spawn(self, coro) -> Job:
        # The method is not a coroutine
        # but let's keep it async for sake of future changes
        # Migration from function to coroutine is a pain
        return self.spawn_nowait(coro)

    def spawn_nowait(self, coro) -> Job:
        """
        Synchronous version of `spawn`.
        """
        return self._spawn_nowait(coro)

    async def close(self):
        if self._closed:
            return
        self._closed = True  # prevent adding new jobs

        jobs = self._jobs
        if jobs:
            # cleanup pending queue
            # all job will be started on closing
            self._pending.clear()
            await asyncio.gather(
                *[job._close(self._close_timeout) for job in jobs],
                loop=self._loop, return_exceptions=True)
            self._jobs.clear()
        self._failed_tasks.put_nowait(None)
        await self._failed_task

    def call_exception_handler(self, context):
        handler = self._exception_handler
        if handler is None:
            handler = self._loop.call_exception_handler(context)
        else:
            handler(self, context)

    @property
    def exception_handler(self):
        return self._exception_handler

    def _spawn_nowait(self, coro) -> Job:
        """
        Common (synchronous) job-spawning code.
        """
        if self._closed:
            raise RuntimeError("Scheduling a new job after closing")
        job = Job(coro, self, self._loop)
        should_start = (self._limit is None or
                        self.active_count < self._limit)
        self._jobs.add(job)
        if should_start:
            job._start()
        else:
            self._pending.append(job)
        return job

    def _done(self, job):
        self._jobs.discard(job)
        if not self._pending:
            return
        # No pending jobs when limit is None
        # Safe to subtract.
        ntodo = self._limit - self.active_count
        i = 0
        while i < ntodo:
            if not self._pending:
                return
            new_job = self._pending.popleft()
            if new_job.closed:
                continue
            new_job._start()
            i += 1

    async def _wait_failed(self):
        # a coroutine for waiting failed tasks
        # without awaiting for failed tasks async raises a warning
        while True:
            task = await self._failed_tasks.get()
            if task is None:
                return  # closing
            try:
                await task  # should raise exception
            except Exception as exc:
                # Cleanup a warning
                # self.call_exception_handler() is already called
                # by Job._add_done_callback
                # Thus we caught an task exception and we are good citizens
                pass
