#!/usr/bin/env python3
import asyncio
import sys

class JobProtocol(asyncio.SubprocessProtocol):
    def __init__(self, exit_future, stdout_future, stderr_future):
        self.exit_future = exit_future
        self.stdout_future = stdout_future
        self.stderr_future = stderr_future

    def pipe_data_received(self, fd, data):
        if fd == 1:
            self.stdout_future.set_result(data)
        if fd == 2:
            self.stderr_future.set_result(data)
        if fd < 0 or fd > 2:
            raise ValueError('Unknown fd number "{}"'.format(fd))

    def process_exited(self):
        self.exit_future.set_result(True)

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

    async def start(self, loop):
        # Create the subprocess controlled by the protocol DateProtocol,
        # redirect the standard output into a pipe
        create = loop.subprocess_exec(lambda:
                                      JobProtocol(exit_future=self.finish_future,
                                                  stdout_future=self.stdout_future,
                                                  stderr_future=self.stderr_future),
                                      *self.command,
                                      stdin=None)
        self.stdout_future.add_done_callback(self.default_stdout_handler)
        self.stderr_future.add_done_callback(self.default_stderr_handler)        
        asyncio.ensure_future(self.finish_future)
        transport, protocol = await create
        print('Process started, pid="{}"'.format(transport.get_pid()))
        self.start_future.set_result( (transport, protocol) )

    def default_stdout_handler(self, future):
        data = future.result()
        print(data)
        if self.save_stdout:
            self.stdout.extend(bytest(data))
        future = asyncio.Future(loop=loop)
        future.add_done_callback(self.default_stdout_handler)

    def default_stderr_handler(self, future):
        data = future.result()
        print(data)
        if self.save_stderr:
            self.stderr.extend(bytes(data))
        future.add_done_callback(self.default_stderr_handler)

    def default_finish_handler(self, future):
        (transport, protocol) = future.result()
        print('Process finished, pid="{}"'.format(transport.get_pid()))
        transport.close()

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

j = job(loop)
j.command(['test2.sh', '5'])
asyncio.ensure_future(j.start(loop))
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
