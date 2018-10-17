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
