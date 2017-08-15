.. _aiojobs-intro:

Introduction
============

.. currentmodule:: aiojobs


Rationale
---------

Asyncio has builtin support for starting new tasks.

But for many reasons raw tasks are not sufficient for daily needs:

#. *Fire-and-forget* call like ``loop.create_task(f())`` doesn't give
   control about errors raised from ``f()`` async function: all
   exceptions are thrown into
   :meth:`asyncio.AbstractEventLoop.call_exception_handler`.
#. Tasks are not grouped into a
   container. :meth:`asyncio.Task.get_tasks()` gets all of them but it
   is not very helpful: typical asyncio program creates a lot of
   internal tasks.
#. Graceful shutdown requires correct cancellation for task spawned by user.
#. Very often a limit for amount of concurrent user tasks a desirable
   to prevent over-flooding.

Web servers like :mod:`aiohttp.web` introduces more challenges: a code
executed by :term:`web-handler` might be closed at every ``await`` by
HTTP client disconnection.

Sometimes it is desirable behavior. If server makes long call to
database on processing GET HTTP request and the request is cancelled
there is no reason to continue data collecting: output HTTP channel is
closed anyway.

But sometimes HTTP POST processing requires atomicity: data should be
put into DB or sent to other server regardless of HTTP client
disconnection. It could be done by spawning a new task for data
sending but see concerns above.

Solution
--------

:mod:`aiojobs` provides two concepts: *Job* and *Scheduler*.

Job is a wrapper around asyncio task. Jobs could be spawned
to start async function execution, awaited for result/exception
and closed.

Scheduler is a container for spawned jobs with implied concurrency
limit.

Scheduler's jobs could be enumerated and closed.

There is simple usage example::

   scheduler = await aiojobs.create_scheduler()

   job = scheduler.spawn(f())

   await scheduler.close()

Every job could be explicitly awaited for its result or closed::

   result = await job.wait(timeout=5.0)

   result = await job.close()

All exceptions raised by job's async function are propagated to caller
by explicit :meth:`Job.wait()` and :meth:`Job.close()` calls.

In case of *fire-and-forget* ``scheduler.spawn(f())`` call without
explicit awaiting the error is passed to
:meth:`Scheduler.call_exception_handler` for logging.

Concurrency limit
-----------------

The :class:`Scheduler` has implied limit for amount of concurrent jobs
(``100`` by default).

Suppose we have 100 active jobs already. Next :meth:`Scheduler.spawn`
call pushed a new job into pending list. Once one of already running
jobs stops next job from pending list is executed.

It prevents a program over-flooding by running a billion of jobs at
the same time.

The limit could be relaxed by passing *limit* parameter into
:func:`create_scheduler`: ``await
aiojobs.create_scheduler(limit=100000)`` or even disabled by
``limit=None``.

Graceful Shutdown
-----------------

All spawned jobs are stopped and closed by :meth:`Scheduler.close()`.

The call has a timeout for waiting for close:
:attr:`Scheduler.close_timeout` (``0.1`` second by default).

If spawned job's closing time takes more than timeout a message is logged by
:meth:`Scheduler.call_exception_handler`.

Close timeout could be overridden by :func:`create_scheduler`: ``await
aiojobs.create_scheduler(close_timeout=10)``


Introspection
--------------

A scheduler is container for jobs.


Atomicity
---------

The library has no guarantee for job execution starting.

The problem is::

   task = loop.create_task(coro())
   task.cancel()

cancels a task immediately, a code from ``coro()`` has no chance to
be executed.

Adding a context switch like ``asyncio.sleep(0)`` between
``create_task()`` and ``cancel()`` calls doesn't solve the problem:
callee could be cancelled on waiting for ``sleep()`` also.

Thus shielding an async function ``task =
loop.create_task(asyncio.shield(coro()))`` still doesn't guarantee
that ``coro()`` will be executed if callee is cancelled.
