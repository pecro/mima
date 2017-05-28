#!/usr/bin/env python3
import asyncio
import sys

# job.start()
# job.add_start_callback()
# job.cancel()
# job.status(), scheduled, not_started, running, timed_out, canceled, terminated, finished
# job.
# job.pause() ??
#
class job:
    def __init__(self, loop, save_stdout=False, save_stderr=False, save_mixed=False, limit=(1024*4)):
        self.loop = loop
        #self.stdout = bytearray()
        #self.stderr = bytearray()
        self.save_stdout = save_stdout
        self.save_stderr = save_stderr
        self.save_mixed = save_mixed
        self.buf_stdout = bytearray()
        self.buf_stderr = bytearray()
        self.buf_mixed = bytearray()
        self.limit = limit
        self.tasks = list()

    def command(self, *args):
        self.command = args

    async def run(self):
        create = asyncio.create_subprocess_exec(
            *self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        self.process = await create
        print('Process start: {}'.format(self.process.pid))
        if self.save_mixed:
            self.tasks.append(self.loop.create_task(self.stdout_saver()))
            self.tasks.append(self.loop.create_task(self.stderr_saver()))
        else:
            if self.save_stdout:
                self.tasks.append(self.loop.create_task(self.stdout_saver()))
            if self.save_stderr:
                self.tasks.append(self.loop.create_task(self.stderr_saver()))

    async def stdout_saver(self):
        while True:
            data = await self.stdout()
            if not data:
                break
            if self.save_mixed:
                self.buf_mixed.extend(data)
            if self.save_stdout:
                self.buf_stdout.extend(data)

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
        await self.process.wait()
        print('Process end: {}'.format(self.process.pid))

    async def print_stdout(self):
        async for data in self.process.read():
            print(data)

    async def stdout(self):
        data = await self.process.stdout.read(self.limit)
        return data

    async def stderr(self):
        data = await self.process.stderr.read(self.limit)
        return data

    async def output(self):
        data = await self.process.read()
        return data

    def default_output_handler(self, data, save, buf):
        print(data.decode('ascii'))
        if save:
            buf.extend(data)

    def default_stdout_handler(self, data):
        self.default_output_handler(b'stdout: ' + data, self.save_stdout, self.stdout)

    def default_stderr_handler(self, data):
        self.default_output_handler(b'stderr: ' + data, self.save_stderr, self.stderr)

class chunk:
    def __init__(self, j):
        self.j = j

    def __aiter__(self):
        return self

    @asyncio.coroutine
    def __anext__(self):
        val = yield from self.j.process.stdout.read(1000)
        if val == b'':
            raise StopAsyncIteration
        return val

#@asyncio.coroutine
#def chunk(j):
#    yield from j.process.read()

#async def printer(j):
#    ch = chunk(j)
#    async for data in ch:
#        print('*** stdout ***')
#        print(data.decode().rstrip())
#    return 'fin'

async def printer(io, name):
    while True:
        data = await io()
        if not data:
            break
        print('*** {} ***'.format(name))
        print(data.decode().rstrip())

#async def printer(j,fd):
#    if fd == 1:
#         data = await j.stdout()
#         print('*** stdout ***')
#         print(data)
#    if fd == 2:
#        async for data in j.stderr():
#            print('*** stderr ***')
#            print(data)
#    if fd == 3:
#        async for data in j.output():
#            print('*** either ***')
#            print(data)

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
    await j.run()
    await j.finish()
    print_bufs(j)
    j = job(loop, save_stderr=True)
    j.command('./test2.sh', '5')
    await j.run()
    await j.finish()
    print_bufs(j)
    j = job(loop, save_mixed=True)
    j.command('./test2.sh', '5')
    await j.run()
    await j.finish()
    print_bufs(j)
    
async def main(loop):
    j = job(loop, save_stdout=True, save_stderr=True)
    j.command('./test2.sh', '5')
    await j.run()
    print('job started: {}'.format(j.process.pid))
    #asyncio.ensure_future(printer(j))
    loop.create_task(printer(j.stdout, 'STDOUT'))
    loop.create_task(printer(j.stderr, 'STDERR'))
    await j.finish()
    print('job finished: {}'.format(j.process.pid))

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

#f = asyncio.Future(loop=loop)
results = loop.run_until_complete(test_buf_saves(loop))
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
