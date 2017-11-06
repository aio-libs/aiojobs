.. aiojobs documentation master file, created by
   sphinx-quickstart on Sat Jul  1 15:24:45 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

aiojobs: Jobs scheduler for managing background task
====================================================

The library gives controlled way for scheduling background tasks for
:mod:`asyncio` applications.

Installation
------------

.. code-block:: bash

   $ pip3 install aiojobs

Usage example
-------------

.. code-block:: python

   import asyncio
   import aiojobs

   async def coro(timeout):
       await asyncio.sleep(timeout)

   async def main():
       scheduler = await aiojobs.create_scheduler()
       for i in range(100):
           # spawn jobs
           await scheduler.spawn(coro(i/10))

       await asyncio.sleep(5.0)
       # not all scheduled jobs are finished at the moment

       # gracefully close spawned jobs
       await scheduler.close()

   asyncio.get_event_loop().run_until_complete(main())

For further information read :ref:`aiojobs-quickstart`,
:ref:`aiojobs-intro` and :ref:`aiojobs-api`.

Integration with aiohttp.web
----------------------------

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

or just

.. code-block:: python

   from aiojobs.aiohttp import atomic

   @atomic
   async def handler(request):
       return web.Response()

Source code
-----------

The project is hosted on GitHub: https://github.com/aio-libs/aiojobs

Please feel free to file an issue on the bug tracker if you have found
a bug or have some suggestion in order to improve the library.


Communication channels
----------------------

*aio-libs* google group: https://groups.google.com/forum/#!forum/aio-libs

Feel free to post your questions and ideas here.

*Gitter Chat* https://gitter.im/aio-libs/Lobby

We support `Stack Overflow <https://stackoverflow.com>`_.
Please add *python-asyncio* or *aiohttp* tag to your question there.


Author and License
-------------------

The ``aiojobs`` package is written by Andrew Svetlov.

It's *Apache 2* licensed and freely available.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   intro
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
