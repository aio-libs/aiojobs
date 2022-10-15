=======
aiojobs
=======
.. image:: https://travis-ci.org/aio-libs/aiojobs.svg?branch=master
    :target: https://travis-ci.org/aio-libs/aiojobs
.. image:: https://codecov.io/gh/aio-libs/aiojobs/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/aiojobs
.. image:: https://img.shields.io/pypi/v/aiojobs.svg
    :target: https://pypi.python.org/pypi/aiojobs
.. image:: https://readthedocs.org/projects/aiojobs/badge/?version=latest
    :target: http://aiojobs.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://badges.gitter.im/Join%20Chat.svg
    :target: https://gitter.im/aio-libs/Lobby
    :alt: Chat on Gitter

Job scheduler for managing background tasks (asyncio)


The library gives a controlled way for scheduling background tasks for
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
       scheduler = aiojobs.Scheduler()
       for i in range(100):
           # spawn jobs
           await scheduler.spawn(coro(i/10))

       await asyncio.sleep(5.0)
       # not all scheduled jobs are finished at the moment

       # gracefully close spawned jobs
       await scheduler.close()

   asyncio.get_event_loop().run_until_complete(main())


Integration with aiohttp.web
============================

.. code-block:: python

   from aiohttp import web
   from aiojobs.aiohttp import setup, spawn

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

For more information read documentation: https://aiojobs.readthedocs.io

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
