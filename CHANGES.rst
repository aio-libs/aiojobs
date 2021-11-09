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
