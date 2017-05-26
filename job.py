#!/usr/bin/env python3
import asyncio
import sys

class JobProtocol(asyncio.SubprocessProtocol):
    def __init__(self, j):
        self.j = j
        self.done_future = asyncio.Future(loop=j.loop)

    def pipe_data_received(self, fd, data):
        if fd == 1:
            self.j.default_stdout_handler(data)
        if fd == 2:
            self.j.default_stderr_handler(data)
        if fd < 0 or fd > 2:
            raise ValueError('Unknown fd number "{}"'.format(fd))

    def process_exited(self):
        self.done_future.set_result(True)

    @asyncio.coroutine
    def done(self):
        asyncio.ensure_future(self.done_future)
        yield from self.done_future

def on_pid(future):
    pid = future.result()
    print('pid={}'.format(pid))

def on_date(future):
    date = future.result()
    print('date="{}"'.format(date.decode('ascii').rstrip()))

# job.start()
# job.add_start_callback()
# job.cancel()
# job.status(), scheduled, not_started, running, timed_out, canceled, terminated, finished
# job.
# job.pause() ??
#
class job:
    def __init__(self, loop, save_stdout=False, save_stderr=False):
        self.loop = loop
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.save_stdout = save_stdout
        self.save_stderr = save_stderr
        self.stdout_future = asyncio.Future(loop=loop)
        self.stderr_future = asyncio.Future(loop=loop)
        self.start_future = asyncio.Future(loop=loop)
        self.finish_future = asyncio.Future(loop=loop)

    def command(self, value):
        self.command = value

    def __await__(self):
        create = self.loop.subprocess_exec(lambda:
                                           JobProtocol(self),
                                           *self.command,
                                           stdin=None)
        asyncio.ensure_future(self.finish_future)
        transport, protocol = (yield from create)
        pid=transport.get_pid()
        print('Process started, pid="{}"'.format(pid))
        yield from protocol.done()
        print('process finished, pid="{}"'.format(pid))

    async def start(self, loop):
        # Create the subprocess controlled by the protocol DateProtocol,
        # redirect the standard output into a pipe
        create = loop.subprocess_exec(lambda:
                                      JobProtocol(self),
                                      *self.command,
                                      stdin=None)
        asyncio.ensure_future(self.finish_future)
        transport, protocol = await create
        print('Process started, pid="{}"'.format(transport.get_pid()))
        self.start_future.set_result( (transport, protocol) )

    def default_output_handler(self, data, save, buf):
        print(data.decode('ascii'))
        if save:
            buf.extend(data)

    def default_stdout_handler(self, data):
        self.default_output_handler(data, self.save_stdout, self.stdout)

    def default_stderr_handler(self, future):
        self.default_output_handler(data, self.save_stderr, self.stderr)

    def default_finish_handler(self):
        (transport, protocol) = self.start_future.result()
        print('Process finished, pid="{}"'.format(transport.get_pid()))
        transport.close()
        print('STDOUT')
        print('------')
        print(self.stdout.decode('ascii'))
        print('STDERR')
        print('------')
        print(self.stderr.decode('ascii'))
        self.loop.stop()

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

j = job(loop, save_stdout=True, save_stderr=True)
j.command(['test2.sh', '5'])
asyncio.ensure_future(j)
results = loop.run_forever()
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
