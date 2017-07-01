import asyncio
import traceback
import sys

import async_timeout


class Job:
    _source_traceback = None
    _closed = False
    _explicit = False
    _task = None

    def __init__(self, coro, scheduler, loop):
        self._loop = loop
        self._coro = coro
        self._scheduler = scheduler

        if loop.get_debug():
            self._source_traceback = traceback.extract_stack(sys._getframe(2))

    def __repr__(self):
        info = []
        if self._closed:
            info.append('closed')
        elif self._task is None:
            info.append('pending')
        info = ' '.join(info)
        if info:
            info += ' '
        return '<Job {}coro=<{}>>'.format(info, self._coro)

    @property
    def closed(self):
        return self._closed

    @property
    def pending(self):
        return self._task is None and not self.closed

    @property
    def active(self):
        return not self.closed and not self.pending

    async def wait(self, timeout=None):
        self._explicit = True
        try:
            with async_timeout.timeout(timeout=timeout, loop=self._loop):
                return await self._task
        except Exception as exc:
            await self.close()
            raise exc

    async def close(self, *, timeout=None, _explicit=True):
        if self._closed:
            return
        self._closed = True
        if self._task is None:
            # the task is closed immediately without actual execution
            # it prevents a warning like
            # RuntimeWarning: coroutine 'coro' was never awaited
            self._start()
        if not self._task.done():
            self._task.cancel()
        # self._scheduler is None after _done_callback()
        scheduler = self._scheduler
        if timeout is None:
            timeout = self._scheduler.close_timeout
        try:
            with async_timeout.timeout(timeout=timeout,
                                       loop=self._loop):
                await self._task
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError as exc:
            if _explicit:
                raise
            context = {'message': "Job closing timed out",
                       'job': self,
                       'exception': exc}
            if self._source_traceback is not None:
                context['source_traceback'] = self._source_traceback
            scheduler.call_exception_handler(context)
        except Exception as exc:
            if _explicit:
                raise
            self._report_exception(exc)

    def _start(self):
        if self._task is not None:
            return  # already started
        self._task = self._loop.create_task(self._coro)
        self._task.add_done_callback(self._done_callback)

    def _done_callback(self, task):
        scheduler = self._scheduler
        scheduler._done(self, False)
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            pass
        else:
            if exc is not None and not self._explicit:
                self._report_exception(exc)
                scheduler._failed_tasks.put_nowait(task)
        self._scheduler = None  # drop backref
        self._closed = True

    def _report_exception(self, exc):
        context = {'message': "Job processing failed",
                   'job': self,
                   'exception': exc}
        if self._source_traceback is not None:
            context['source_traceback'] = self._source_traceback
        self._scheduler.call_exception_handler(context)
