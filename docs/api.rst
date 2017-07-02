.. module:: aiojobs

.. currentmodule:: aiojobs

API
===

Instantiation
-------------

.. cofunction:: create_scheduler(*, close_timeout=0.1, limit=100,
                                 exception_handler=None)

   Create a new :class:`Scheduler`.

   * *timeout* is a timeout for job closing, ``0.1`` by default.

   * *limit* is a for jobs spawned by scheduler, ``100`` by
     default. If spawned job's closing time takes more than timeout a
     message is logged by :meth:`Scheduler.call_exception_handler`.

   * *exception_handler* is a callable with
     ``handler(scheduler, context)`` signature to log
     unhandled exceptions from jobs (see
     :meth:`Scheduler.call_exception_handler` for documentation about
     *context* and default implementaion).


Scheduler
---------

.. class:: Scheduler

   A container for managed jobs.

   Jobs are created by :meth:`spawn()`.

   :meth:`close` should be used for finishing all scheduled jobs.

   The class supports :class:`containers.abc.Container` contract: jobs
   could be iterated etc.

   User should never instantiate the class but call
   :func:`create_scheduler` async function.

   .. attribute:: limit

      Concurrency limit (``100`` by default) or ``None`` if the limit
      is disabled. See :func:`create_scheduler` for setting the attribute.

   .. attribute:: close_timeout

      Timeout for waiting for jobs closing, ``0.1`` by default.

   .. attribute:: active_count

      Count of active (executed) jobs.

   .. attribute:: pending_count

      Count of scheduled but not executed yet jobs.


   .. comethod:: spawn(coro)

      Spawn a new job for execution *coro* coroutine.

      Return a new :class:`Job` object.

      The job might be started immediately of pushed into pending list
      if concurrency limit (:attr:`limit`) exceeded.


   .. comethod:: close()

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
