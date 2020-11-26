"""Jobs scheduler for managing background task (asyncio).

The library gives controlled way for scheduling background tasks for
asyncio applications.

"""


__version__ = '0.3.0'

import asyncio

from ._scheduler import Scheduler


async def create_scheduler(*, close_timeout=0.1, limit=100,
                           pending_limit=10000, exception_handler=None):
    if exception_handler is not None and not callable(exception_handler):
        raise TypeError('A callable object or None is expected, '
                        'got {!r}'.format(exception_handler))
    loop = asyncio.get_event_loop()
    return Scheduler(loop=loop, close_timeout=close_timeout,
                     limit=limit, pending_limit=pending_limit,
                     exception_handler=exception_handler)

__all__ = ('create_scheduler',)
