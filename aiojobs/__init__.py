__version__ = '0.0.3'

import asyncio
from ._scheduler import Scheduler


async def create_scheduler(*,
                           close_timeout=0.1,
                           limit=100,
                           exception_handler=None,
                           loop=None):
    if exception_handler is not None and not callable(exception_handler):
        raise TypeError('A callable object or None is expected, '
                        'got {!r}'.format(exception_handler))
    loop = loop or asyncio.get_event_loop()
    return Scheduler(loop=loop,
                     close_timeout=close_timeout,
                     limit=limit,
                     exception_handler=exception_handler)

__all__ = ('create_scheduler',)
