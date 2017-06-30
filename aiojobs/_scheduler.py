import asyncio
from collections import deque
from collections.abc import Container

from ._job import Job


class Scheduler(Container):
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

    async def spawn(self, coro):
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
    def closed(self):
        return self._closed

    async def close(self):
        if self._closed:
            return
        self._closed = True  # prevent adding new jobs

        jobs = self._jobs
        if jobs:
            await asyncio.gather(
                *[job.close(timeout=self._close_timeout) for job in jobs],
                loop=self._loop, return_exceptions=True)
        self._pending.clear()
        self._jobs.clear()
        self._failed_tasks.put_nowait(None)
        await self._failed_task

    @property
    def limit(self):
        return self._limit

    @property
    def active_count(self):
        return len(self._jobs) - len(self._pending)

    @property
    def pending_count(self):
        return len(self._pending)

    @property
    def close_timeout(self):
        return self._close_timeout

    def call_exception_handler(self, context):
        handler = self._exception_handler
        if handler is None:
            handler = self._loop.call_exception_handler(context)
        else:
            handler(self, context)

    @property
    def exception_handler(self):
        return self._exception_handler

    def _done(self, job, pending):
        self._jobs.remove(job)
        if pending:
            self._pending.remove(job)
        if not self._pending:
            return
        if self._limit is None:
            ntodo = len(self._pending)
        else:
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
