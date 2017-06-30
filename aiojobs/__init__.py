__version__ = '0.0.1'

import asyncio
from ._scheduler import _Scheduler


async def create_scheduler(*, close_timeout=0.1, concurrency=100,
                           exception_handler=None):
    if exception_handler is not None and not callable(exception_handler):
        raise TypeError('A callable object or None is expected, '
                        'got {!r}'.format(exception_handler))
    loop = asyncio.get_event_loop()
    return _Scheduler(loop=loop, close_timeout=close_timeout,
                      concurrency=concurrency,
                      exception_handler=exception_handler)

__all__ = ('create_scheduler',)
