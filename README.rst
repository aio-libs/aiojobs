=======
aiojobs
=======

Jobs scheduler for managing background task (asyncio)


The library gives controlled way for scheduling background tasks for
asyncio applications.

Installation
============

.. code-block:: bash

   $ pip3 install aiojobs

Usage example
=============

.. code-block:: python

   import asyncio
   import aiojobs

   async def coro(timeout):
       await asyncio.sleep(timeout)

   async def main():
       scheduler = aiojobs.create_scheduler()
       for i in range(100):
           # spawn jobs
           await scheduler.spawn(coro(i/10))

       await asyncio.sleep(5.0)
       # not all scheduled jobs are finished at the moment

       # gracefuly close spawned jobs
       await scheduler.close()

   asyncio.get_event_loop().run_until_complete(main())


Integration with aiohttp.web
============================

.. code-block:: python

   from aiohttp import web
   from aiojobs.aiohttp import setup, spawn
   import aiojobs

   async def handler(request):
       await spawn(requenst, coro())
       return web.Response()

   app = web.Application()
   app.router.add_get('/', handler)
   setup(app)


For more information read documentaion: https://aiojobs.readthedocs.io

Communication channels
======================

*aio-libs* google group: https://groups.google.com/forum/#!forum/aio-libs

Feel free to post your questions and ideas here.

*Gitter Chat* https://gitter.im/aio-libs/Lobby

We support `Stack Overflow <https://stackoverflow.com>`_.
Please add *python-asyncio* or *aiohttp* tag to your question there.


Author and License
==================

The ``aiojobs`` package is written by Andrew Svetlov.

It's *Apache 2* licensed and freely available.
