import asyncio


async def test_job_spawned(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    assert job.active
    assert not job.closed
    assert not job.pending
    assert 'closed' not in repr(job)
    assert 'pending' not in repr(job)


async def test_job_awaited(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    await job.wait()

    assert not job.active
    assert job.closed
    assert not job.pending
    assert 'closed' in repr(job)
    assert 'pending' not in repr(job)


async def test_job_closed(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    await job.close()

    assert not job.active
    assert job.closed
    assert not job.pending
    assert 'closed' in repr(job)
    assert 'pending' not in repr(job)


async def test_job_pending(make_scheduler):
    scheduler = make_scheduler(limit=1)

    async def coro1():
        await asyncio.sleep(10)

    async def coro2():
        pass

    await scheduler.spawn(coro1())
    job = await scheduler.spawn(coro2())

    assert not job.active
    assert not job.closed
    assert job.pending
    assert 'closed' not in repr(job)
    assert 'pending' in repr(job)


async def test_job_resume_after_p_e_nding(make_scheduler):
    # Mangle a name for satisfy 'pending' not in repr check
    scheduler = make_scheduler(limit=1)

    async def coro1():
        await asyncio.sleep(10)

    async def coro2():
        pass

    job1 = await scheduler.spawn(coro1())
    job2 = await scheduler.spawn(coro2())

    await job1.close()

    assert job2.active
    assert not job2.closed
    assert not job2.pending
    assert 'closed' not in repr(job2)
    assert 'pending' not in repr(job2)
