=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "changes".

    WARNING: Don't drop the next directive!

.. towncrier release notes start

1.1.0 (2022-10-16)
==================

Features
--------

- Complete type annotations have been added. (`#352 <https://github.com/aio-libs/aiojobs/pull/352>`_)
- ``Scheduler`` can (and should be) instantiated directly. (`#353 <https://github.com/aio-libs/aiojobs/pull/353>`_)
- ``Job`` is also exported by default now, to aid type annotations. (`#355 <https://github.com/aio-libs/aiojobs/pull/355>`_)

Bugfixes
--------

- Fix scheduler blocking forever when pending limit is reached. (`#135 <https://github.com/aio-libs/aiojobs/pull/135>`_)
- Fix @atomic wrapper not passing ``self`` to methods. (`#344 <https://github.com/aio-libs/aiojobs/pull/344>`_)
- ``Job.wait()`` now returns the task value if the job is already closed. (`#343 <https://github.com/aio-libs/aiojobs/pull/343>`_)
- Fix ``exception_handler`` being called twice in some situations. (`#354 < https://github.com/aio-libs/aiojobs/pull/354`_)

Deprecations and Removals
-------------------------

- Dropped Python 3.6 support. (`#338 <https://github.com/aio-libs/aiojobs/pull/338>`_)
- ``create_scheduler()`` is deprecated and will be removed in v2. (`#353 <https://github.com/aio-libs/aiojobs/pull/353>`_)


1.0.0 (2021-11-09)
==================

Features
--------

- Switch to ``async-timeout>=4.0.0``. (`#275 <https://github.com/aio-libs/aiojobs/issues/275>`_)
- Added Python 3.10 support. (`#277 <https://github.com/aio-libs/aiojobs/issues/277>`_)
- Added type hints support. (`#280 <https://github.com/aio-libs/aiojobs/issues/280>`_)


Deprecations and Removals
-------------------------

- Dropped Python 3.5 support. (`#279 <https://github.com/aio-libs/aiojobs/issues/279>`_)


0.3.0 (2020-11-26)
==================

Features
--------

- Make aiohttp as extra requirement (#80)

Bugfixes
--------

- Fix AttributeError when calling wait() or close() on failed job. (#29)


0.2.2 (2018-10-17)
==================

- Fix AttributeError when calling ``wait()`` or ``close()`` on failed job (#64)

0.2.1 (2018-03-10)
==================

- Add missing decription file

0.2.0 (2018-03-10)
==================

Features
--------

- Add a new scheduler parameter for control pending jobs size. (#19)

- Cancelling a task suspended on ``job.wait()`` doesn't cancel inner
job task but timeout exemption does. (#28)

Bugfixes
--------

- Fix AttributeError when `@atomic` decorator is used in Class Based Views.
  (#21)
