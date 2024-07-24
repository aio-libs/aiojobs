.. _aiojobs-quickstart:

Quickstart
==========

.. currentmodule:: aiojobs


The library gives controlled way for scheduling background tasks.

Installation
-------------

Install the library:

.. code-block:: bash

   $ pip3 install aiojobs

Simple example
----------------

The library API is pretty minimalistic: make a scheduler, spawn jobs,
close scheduler.

Instantiate a scheduler::

   import aiojobs

   scheduler = aiojobs.Scheduler()

Spawn a new job::

   await scheduler.spawn(coro())

At the end of program gracefully close the scheduler::

   await scheduler.wait_and_close()


Let's collect it altogether into very small but still functional example::

   import asyncio
   import aiojobs

   async def coro(timeout):
       await asyncio.sleep(timeout)

   async def main():
       async with aiojobs.Scheduler() as scheduler:
           for i in range(100):
               # spawn jobs
               await scheduler.spawn(coro(i/10))

           await asyncio.sleep(5.0)
           # not all scheduled jobs are finished at the moment
       # Exit from context will gracefully wait on tasks before closing
       # any remaining spawned jobs

   asyncio.run(main())


Our jobs are very simple :func:`asyncio.sleep` calls with variable
timeout -- pretty enough for demonstration.

Example schedules ``100`` jobs, every job takes from ``0`` to ``10``
seconds for its execution.

Next we waits for ``5`` seconds. Roughly half of scheduled jobs should
be finished already but ``50`` jobs are still active.

For closing them we exit the context manager, which calls
:meth:`aiojobs.Scheduler.wait_and_close`. This waits for a grace period
to allow tasks to complete normally, then after a timeout it sends
:exc:`asyncio.CancelledError` into every non-closed job to stop them.

Alternatively, we could use :meth:`Scheduler.close` to immediately
close/cancel the jobs.

That's pretty much it.

Integration with aiohttp web server
-----------------------------------

.. currentmodule:: aiojobs.aiohttp

In aiohttp web-handlers might be cancelled at any time on client disconnection.

But sometimes user need to prevent unexpected cancellation of some
code executed by web handler.

Other use case is spawning background tasks like statistics update or
email sending and returning HTTP response as fast as possible.

Both needs could be solved by *aiojobs.aiohttp* integration module.

The library has two helpers: :func:`setup` for installing web
application initialization and finalization hooks and :func:`spawn`
for spawning new jobs:

.. code-block:: python

   from aiohttp import web
   from aiojobs.aiohttp import setup, spawn
   import aiojobs

   async def handler(request):
       await spawn(request, coro())
       return web.Response()

   app = web.Application()
   app.router.add_get('/', handler)
   setup(app)




Future reading
--------------

For more info about library design and principles read :ref:`aiojobs-intro`.

API reference is here: :ref:`aiojobs-api`.
