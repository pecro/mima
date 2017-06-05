#!/usr/bin/env python3
"""
Some documentation for this module
"""


import asyncio
import sys
import psutil
from hurry.filesize import size

# job.start()
# job.add_start_callback()
# job.cancel()
# job.status(), scheduled, not_started, running, timed_out, canceled,
#               terminated, finished
# job.
# job.pause() ??
#

class Refuture:
    def __init__(self):
        self.current = None
        self.next = asyncio.Future()
        asyncio.ensure_future(self.update())
        self.done = False
        self.finished = asyncio.Future()

    async def get_lock(self):
        while self.current.done():
            await asyncio.sleep(0)

    async def update(self):
        while True:
            await asyncio.sleep(0)
            self.current = self.next
            self.next = asyncio.Future()
            if self.done:
                break
            await self.current
        self.finished.set_result(None)


class _Output:
    """A helper class to allow async iteration on process output."""
    def __init__(self, rcvd):
        """rcvd is a Refuture"""
        self.rcvd = rcvd

    def __aiter__(self):
        return self

    @asyncio.coroutine
    def __anext__(self):
        yield from self.rcvd.next
        val = self.rcvd.current.result()
        if val is None:
            raise StopAsyncIteration
        return val


class job:
    def __init__(self, loop, save_stdout=False, save_stderr=False,
                 save_mixed=False, echo=False, limit=(1024*4)):
        self.loop = loop
        self.save_stdout = save_stdout
        self.save_stderr = save_stderr
        self.save_mixed = save_mixed
        self.buf_stdout = bytearray()
        self.buf_stderr = bytearray()
        self.buf_mixed = bytearray()
        self.limit = limit
        self.started = asyncio.Future()
        self.stdout_rcvd = None
        self.stdout_updater_finished = asyncio.Future()
        self.monitor = None

    def command(self, *args):
        self.command = args

    async def start(self):
        create = asyncio.create_subprocess_exec(
            *self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        self.process = await create
        print('Process start: {}'.format(self.process.pid))
        self.stdout_rcvd = Refuture()
        asyncio.ensure_future(self.stdout_updater())
        if self.save_mixed:
            asyncio.ensure_future(self.stdout_saver())
            asyncio.ensure_future(self.stderr_saver())
        else:
            if self.save_stdout:
                asyncio.ensure_future(self.stdout_saver())
            if self.save_stderr:
                asyncio.ensure_future(self.stderr_saver())
        self.started.set_result(None)
        self.monitor = asyncio.ensure_future(treestat(self.process.pid))

    async def stdout_saver(self):
        rcvd = self.stdout_rcvd
        await rcvd.next
        while True:
            data = rcvd.current.result()
            if not data:
                break
            if self.save_mixed:
                self.buf_mixed.extend(data)
            if self.save_stdout:
                self.buf_stdout.extend(data)
            await rcvd.next

    async def stderr_saver(self):
        while True:
            data = await self.stderr()
            if not data:
                break
            if self.save_mixed:
                self.buf_mixed.extend(data)
            if self.save_stderr:
                self.buf_stderr.extend(data)

    async def finish(self):
        await self.started
        await self.process.wait()
        self.monitor.cancel()
        await self.stdout_updater_finished
        print('Process end: {}'.format(self.process.pid))

    async def stdout_updater(self):
        count=1
        rcvd = self.stdout_rcvd
        data = await self.process.stdout.read(self.limit)
        print ('stdout_updater({})'.format(count))
        count += 1
        while data:
            await rcvd.get_lock()
            rcvd.current.set_result(data)
            await asyncio.sleep(0.1)
            data = await self.process.stdout.read(self.limit)
            print ('stdout_updater({})'.format(count))
            count += 1
        rcvd.done = True
        await rcvd.get_lock()
        rcvd.current.set_result(None)
        await rcvd.finished
        self.stdout_updater_finished.set_result(None)

    def stdout_iter(self):
        iter = _Output(self.stdout_rcvd)
        return iter

    async def stdout(self):
        rcvd = self.stdout_rcvd
        await rcvd.next
        return rcvd.current.result()


def get_root_process(pid):
    root = psutil.Process(pid)
    while root.parent():
        print('pid={} has parent'.format(pid))
        root = root.parent()
    return root


async def treestat(pid, interval=5):
    """Periodically report process information."""
    #root = get_root_process(pid)
    root =psutil.Process(pid)
    while True:
        print('{} cpu={} mem={}'.format(root.pid, root.name(), size(root.memory_info()[0])))
        await asyncio.sleep(interval)

async def printer(io, name):
    count = 1
    while True:
        data = await io()
        if not data:
            break
        print('*** {}({}) ***'.format(name, count))
        count += 1
        print(data.decode().rstrip())


def print_bufs(j):
    print('*** SAVED STDOUT ***')
    print(j.buf_stdout.decode())
    print('*** SAVED STDERR ***')
    print(j.buf_stderr.decode())
    print('*** SAVED MIXED ***')
    print(j.buf_mixed.decode())

async def test_buf_saves(loop):
    j = job(loop, save_stdout=True)
    j.command('./test2.sh', '5')
    await j.finish()
    print_bufs(j)
    j = job(loop, save_stderr=True)
    j.command('./test2.sh', '5')
    await j.finish()
    print_bufs(j)
    j = job(loop, save_mixed=True)
    j.command('./test2.sh', '5')
    await j.finish()
    print_bufs(j)
    j = job(loop, save_stdout=True, save_stderr=True, save_mixed=True)
    j.command('./test2.sh', '5')
    await j.finish()
    print_bufs(j)

async def output_with_iter(j):
    async for data in j.stdout_iter():
        print(data.decode())

async def test_async_iteration(loop):
    j = job(loop, save_stdout=True)
    j.command('./test2.sh', '50')
    await j.start()
    asyncio.ensure_future(output_with_iter(j))
    await j.finish()

async def main(loop):
    j = job(loop, save_stdout=True)
    j.command('./test2.sh', '50')
    await j.start()
    print('job started: {}'.format(j.process.pid))
    # asyncio.ensure_future(printer(j))
    asyncio.ensure_future(printer(j.stdout, 'STDOUT'))
    #asyncio.ensure_future(printer(j.stderr, 'STDERR'))
    await j.finish()
    print('job finished: {}'.format(j.process.pid))

if __name__ == "__main__":
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    # f = asyncio.Future(loop=loop)
    # results = loop.run_until_complete(test_buf_saves(loop))
    # loop.run_until_complete(main(loop))
    loop.run_until_complete(test_async_iteration(loop))
    loop.close()

# j.cmd = ['sleep', '1']
# j.add_on_stdout(print_stdout_handler)
# j.add_on_start(print_pid)
# j.add_on_finish(print_finish)
# j.start()

# j = job()
# j.ensure_future(j.stdout_future)
# j.ensure_future(j.stderr_future)
# j.ensure_future(j.start_future)
# j.ensure_future(j.finish_future)
# j.start()
