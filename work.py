#!/usr/bin/env python3
import asyncio
import sys

class DateProtocol(asyncio.SubprocessProtocol):
    def __init__(self, exit_future):
        self.exit_future = exit_future
        self.output = bytearray()

    def pipe_data_received(self, fd, data):
        self.output.extend(data)

    def process_exited(self):
        self.exit_future.set_result(True)


def on_pid(future):
    pid = future.result()
    print('pid={}'.format(pid))

def on_date(future):
    date = future.result()
    print('date="{}"'.format(date.decode('ascii').rstrip()))

class job:
    async def get_date(self, loop):
        date = asyncio.Future(loop=loop)
        date.add_done_callback(on_date)
        await self.exit_future

        # Close the stdout pipe
        self.transport.close()

        # Read the output which was collected by the pipe_data_received()
        # method of the protocol
        date.set_result(bytes(self.protocol.output))

    async def get_pid(self, loop):
        self.exit_future = asyncio.Future(loop=loop)
        self.pid_future = asyncio.Future(loop=loop)
        self.pid_future.add_done_callback(on_pid)

        # Create the subprocess controlled by the protocol DateProtocol,
        # redirect the standard output into a pipe
        create = loop.subprocess_exec(lambda: DateProtocol(self.exit_future),
                                      'test1.sh',
                                      stdin=None, stderr=None)
        transport, protocol = await create
        self.transport = transport
        self.protocol = protocol
        pid = transport.get_pid()
        self.pid_future.set_result(pid)

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

j = job()

asyncio.ensure_future(j.get_pid(loop))
results = loop.run_until_complete(j.get_date(loop))
loop.close()
