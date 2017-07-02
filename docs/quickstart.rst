.. _aiojobs-quickstart:

Quickstart
==========

.. currentmodule:: aiojobs


The library gives controlled way for scheduling background tasks.

Install the library:

.. code-block:: bash

   $ pip3 install aiojobs

The library API is pretty minimalistic: make a scheduler, spawn jobs,
close scheduler.

Instantiate a scheduler::

   import aiojobs

   scheduler = await aiojobs.create_scheduler()

Spawn a new job::

   await scheduler.spawn(coro())

At the end of program gracefuly close the scheduler::

   await scheduler.close()


For more info about library design and principles read :ref:`aiojobs-intro`.

API reference is here: :ref:`aiojobs-api`.
