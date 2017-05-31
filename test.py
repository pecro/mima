#!/usr/bin/env python3

import asyncio

value=7
async def result(f):
    global value
    value += 1
    f.set_result(value)

async def wait_on_result1(f):
#    value = await result()
    await f
    val=f.result()
    print('wait_on_result1 => {}'.format(val))

async def wait_on_result2(f):
    await f
    val=f.result()
    print('wait_on_result2 => {}'.format(val))

async def main():
    await wait_on_result1()
    await wait_on_result2()
    await wait_on_result1()
    await wait_on_result2()
    await wait_on_result1()
    await wait_on_result2()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    f = asyncio.Future()
    asyncio.ensure_future(result(f),loop=loop)
    loop.run_until_complete(asyncio.gather(wait_on_result1(f), wait_on_result2(f)))
    loop.close()
