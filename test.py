#!/usr/bin/env python3

import asyncio

def counter_gen(n):
    val = 0
    while val < n:
        yield val
        val += 1

class refuture:
    def __init__(self):
        self.current = asyncio.Future()
        self.next = asyncio.Future()
        asyncio.ensure_future(self.update())
        self.done = False

    async def update(self):
        while True:
            await self.current
            await asyncio.sleep(0)
            if self.done:
                break
            self.current = self.next
            self.next = asyncio.Future()


class counter_class:
    def __init__(self):
        self.val = 0

    @asyncio.coroutine
    def next(self):
        yield from asyncio.sleep(0.1, self.val)
        self.val += 1

    def __await__(self):
        if self.val > 10:
            return self
        else:
            yield from self.next()

class multi_wait_counter:
    def __init__(self):
        self.val = 0
        #asyncio.ensure_future(self.free_running_generate())
        self.count_list = list()
        self.r = refuture()

    async def free_running_generate(self):
        f = self.r.current
        while True:
            await asyncio.sleep(0.1)
            if self.val < 10:
                #print('free_running_generate: emitting {}'.format(self.val))
                f.set_result(self.val)
                self.val += 1
                f = self.r.next
            else:
                #print('free_running_generate: emitting None')
                f.set_result(None)
                self.r.done = True
                break

    async def finish(self):
        await asyncio.gather(self.free_running_generate(), self.save(), self.print_count())

    async def save(self):
        f = self.r.current
        while True:
            await f
            if f.result() is None:
                break
            self.count_list.append(f.result())
            f = self.r.next

    async def print_count(self):
        f = self.r.current
        while True:
            await f
            if f.result() is None:
                break
            print('print_count: {}'.format(f.result()))
            f = self.r.next

global_count = 0
global_current_count = asyncio.Future()
async def counter_multi():
    global global_count
    global global_current_count
    # print('2. future doneness: {}'.format(f.done()))
    while global_count < 10:
        await asyncio.sleep(0.01)
        # print('3. future doneness: {}'.format(f.done()))
        print('emmitting: {}'.format(global_count))
        global_current_count.set_result(global_count)
        # Give awaiters time to process global_current_count result before wacking it
        await asyncio.sleep(0.01)
        global_current_count = asyncio.Future()
        global_count += 1


@asyncio.coroutine
def count():
    value = 0
    while True:
        if value >= 10:
            break
        yield from asyncio.sleep(0.01, value)
        value += 1
    return value

async def wait_on_result1(f):
#    value = await result()
    await f
    val=f.result()
    print('wait_on_result1 => {}'.format(val))

async def wait_on_result2(f):
    await f
    val=f.result()
    print('wait_on_result2 => {}'.format(val))

@asyncio.coroutine
def test_simple():
    for i in range(0,10):
        value = yield from count()
        print('test_simple: count={}'.format(value))

async def test_class():
    c = counter_class()
    for i in range(0,12):
        value = await c
        print('test_class: count={}'.format(c.val))

async def test_multi_cor_printer1():
    global global_current_count
    while True:
        await global_current_count
        print('test_multi_cor_printer1: count={}'.format(global_current_count.result()))

async def test_multi_cor_printer2():
    global global_current_count
    while True:
        await global_current_count
        print('test_multi_cor_printer2: count={}'.format(global_current_count.result()))

async def test_multi_cor():
    asyncio.ensure_future(test_multi_cor_printer1())
    asyncio.ensure_future(test_multi_cor_printer2())
    while True:
        await counter_multi()

async def wait1(f):
    await f
    print('wait1: {}'.format(f.result()))

async def wait2(f):
    await f
    print('wait2: {}'.format(f.result()))

async def test_two_waiters_on_future():
    f = asyncio.Future()
    asyncio.ensure_future(wait1(f))
    asyncio.ensure_future(wait2(f))
    await asyncio.sleep(0.01)
    f.set_result('worked!')
    # Thought this would be necessary, but I guess the waitn functions finish before the loop ends
    #await asyncio.sleep(0.01)

async def external_printer(c):
    f = c.r.current
    while True:
        await f
        if f.result() is None:
            break
        print('external_printer: count: {}'.format(f.result()))
        f = c.r.next

async def test_multi_waiter_class():
    c = multi_wait_counter()
    asyncio.ensure_future(external_printer(c))
    await c.finish()
    for num in c.count_list:
        print('count_list: {}'.format(num))

async def main():
    await test_simple()
    await test_class()
    await test_two_waiters_on_future()
    await test_multi_waiter_class()
    #await test_multi_cor()

if __name__ == "__main__":
    g = counter_gen(10)
    for num in g:
        print('num={}'.format(num))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
