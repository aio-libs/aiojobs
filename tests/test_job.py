async def test_job_spawned(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    assert 'closed' not in repr(job)
    assert 'pending' not in repr(job)
    assert job.active
    assert not job.closed
    assert not job.pending


async def test_job_awaited(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    await job.wait()

    assert 'closed' in repr(job)
    assert 'pending' not in repr(job)
    assert not job.active
    assert job.closed
    assert not job.pending


async def test_job_closed(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    await job.close()

    assert 'closed' in repr(job)
    assert 'pending' not in repr(job)
    assert not job.active
    assert job.closed
    assert not job.pending


async def test_job_pending(make_scheduler):
    scheduler = await make_scheduler(limit=1)

    async def coro():
        pass
    job = await scheduler.spawn(coro())
    await job.close()

    assert 'closed' in repr(job)
    assert 'pending' not in repr(job)
    assert not job.active
    assert job.closed
    assert not job.pending
