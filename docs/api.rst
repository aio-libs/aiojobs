.. _aiojobs-api:

API
===

.. module:: aiojobs

.. currentmodule:: aiojobs


Instantiation
-------------

.. cofunction:: create_scheduler(*, close_timeout=0.1, limit=100, \
                                 pending_limit=10000, \
                                 exception_handler=None)

   Create a new :class:`Scheduler`.

   * *close_timeout* is a timeout for job closing, ``0.1`` by default.
     If job's closing time takes more than timeout a
     message is logged by :meth:`Scheduler.call_exception_handler`.

   * *limit* is a for jobs spawned by scheduler, ``100`` by
     default.

   * *pending_limit* is a limit for amount of jobs awaiting starting,
     ``10000`` by default. Use ``0`` for infinite pending queue size.

   * *exception_handler* is a callable with
     ``handler(scheduler, context)`` signature to log
     unhandled exceptions from jobs (see
     :meth:`Scheduler.call_exception_handler` for documentation about
     *context* and default implementation).

   .. note::

     *close_timeout* pinned down to ``0.1`` second, it looks too small
     at first glance. But it is a timeout for waiting cancelled
     jobs. Normally job is finished immediately if it doesn't
     swallow :exc:`asyncio.CancelledError`.

     But in last case there is no reasonable timeout with good number
     for everybody, user should pass a value suitable for his
     environment anyway.


Scheduler
---------

.. class:: Scheduler

   A container for managed jobs.

   Jobs are created by :meth:`spawn()`.

   :meth:`close` should be used for finishing all scheduled jobs.

   The class implements :class:`collections.abc.Collection` contract,
   jobs could be iterated etc.: ``len(scheduler)``, ``for job in
   scheduler``, ``job in scheduler`` operations are supported.

   User should never instantiate the class but call
   :func:`create_scheduler` async function.

   .. attribute:: limit

      Concurrency limit (``100`` by default) or ``None`` if the limit
      is disabled. See :func:`create_scheduler` for setting the attribute.

   .. attribute:: pending_limit

      A limit for *pending* queue size (``0`` for unlimited queue).

      See :meth:`spawn` for details.

      .. versionadded:: 0.2

   .. attribute:: close_timeout

      Timeout for waiting for jobs closing, ``0.1`` by default.

   .. attribute:: active_count

      Count of active (executed) jobs.

   .. attribute:: pending_count

      Count of scheduled but not executed yet jobs.

   .. attribute:: closed

      ``True`` if scheduler is closed (:meth:`close` called).

   .. comethod:: spawn(coro)

      Spawn a new job for execution *coro* coroutine.

      Return a new :class:`Job` object.

      The job might be started immediately of pushed into pending list
      if concurrency :attr:`limit` exceeded.

      If :attr:`pending_count` is greater than :attr:`pending_limit`
      and the limit is *finite* (not ``0``) the method suspends
      execution without scheduling a new job (adding it into pending
      queue) until penging queue size will be reduced to have a free
      slot.

      .. versionchanged:: 0.2

         The method respects :attr:`pending_limit` now.

   .. comethod:: close()

      Close scheduler and all its jobs.

      It finishing time for particular job exceeds
      :attr:`close_timeout` this job is logged by
      :meth:`call_exception_handler`.


   .. attribute:: exception_handler

      A callable with signature ``(scheduler, context)`` or ``None``
      for default handler.

      Used by :meth:`call_exception_handler`.

   .. method:: call_exception_handler(context)

      Log an information about errors in not explicitly awaited jobs
      and jobs that close procedure exceeds :attr:`close_timeout`.

      By default calls
      :meth:`asyncio.AbstractEventLoop.call_exception_handler`, the
      behavior could be overridden by passing *exception_handler*
      parameter into :func:`create_scheduler`.

      *context* is a :class:`dict` with the following keys:

      * *message*: error message, :class:`str`
      * *job*: failed job, :class:`Job` instance
      * *exception*: caught exception, :exc:`Exception` instance
      * *source_traceback*: a traceback at the moment of job creation
        (present only for debug event loops, see also
        :envvar:`PYTHONASYNCIODEBUG`).


Job
---

.. class:: Job

   A wrapper around spawned async function.

   Job has three states:

     * *pending*: spawn but not executed yet because of concurrency limit
     * *active*: is executing now
     * *closed*: job has finished or stopped.

   All exception not explicitly awaited by :meth:`wait` and
   :meth:`close` are logged by
   :meth:`Scheduler.call_exception_handler`

   .. attribute:: active

      Job is executed now

   .. attribute:: pending

      Job was spawned by actual execution is delayed because
      *scheduler* reached concurrency limit.

   .. attribute:: closed

      Job is finished.

   .. comethod:: wait(*, timeout=None)

      Wait for job finishing.

      If *timeout* exceeded :exc:`asyncio.TimeoutError` raised.

      The job is in *closed* state after finishing the method.

   .. comethod:: close(*, timeout=None)

      Close the job.

      If *timeout* exceeded :exc:`asyncio.TimeoutError` raised.

      The job is in *closed* state after finishing the method.

Integration with aiohttp web server
-----------------------------------

.. module:: aiojobs.aiohttp

.. currentmodule:: aiojobs.aiohttp


For using the project with *aiohttp* server a scheduler should be
installed into app and new function should be used for spawning new
jobs.

.. function:: setup(app, **kwargs)

   Register :attr:`aiohttp.web.Application.on_startup` and
   :attr:`aiohttp.web.Application.on_cleanup` hooks for creating
   :class:`aiojobs.Scheduler` on application initialization stage and
   closing it on web server shutdown.

   * *app* - :class:`aiohttp.web.Application` instance.
   * *kwargs* - additional named parameters passed to
     :func:`aiojobs.create_scheduler`.

.. cofunction:: spawn(request, coro)

   Spawn a new job using scheduler registered into ``request.app``,
   or a parent :attr:`aiohttp.web.Application`.

   * *request* -- :class:`aiohttp.web.Request` given from :term:`web-handler`
   * *coro* a coroutine to be executed inside a new job

   Return :class:`aiojobs.Job` instance


Helpers

.. function:: get_scheduler(request)

   Return a scheduler from request, raise :exc:`RuntimeError` if
   scheduler was not registered on application startup phase (see
   :func:`setup`). The scheduler will be resolved from the current
   or any parent :attr:`aiohttp.web.Application`, if available.


.. function:: get_scheduler_from_app(app)

   Return a scheduler from aiohttp application or ``None`` if
   scheduler was not registered on application startup phase (see
   :func:`setup`).

.. function:: get_scheduler_from_request(request)

   Return a scheduler from aiohttp request or ``None`` if
   scheduler was not registered on any application in the
   hierarchy of parent applications (see :func:`setup`)

.. decorator:: atomic

   Wrap a web-handler to execute the entire handler as a new job.

   .. code-block:: python

      @atomic
      async def handler(request):
          return web.Response()

   is a functional equivalent of


   .. code-block:: python

      async def inner(request):
          return web.Response()

      async def handler(request):
          job = await spawn(request, inner(request))
          return await job.wait()
