#!/usr/bin/env python3

import asyncio

value=7
async def result():
    global value
    await asyncio.sleep(0.1)
    value += 1
    return value

async def wait_on_result1():
#    value = await result()
    print('wait_on_result1 => {}'.format(await result()))

async def wait_on_result2():
    value = await result()
    print('wait_on_result2 => {}'.format(value))

async def main():
    await wait_on_result1()
    await wait_on_result2()
    await wait_on_result1()
    await wait_on_result2()
    await wait_on_result1()
    await wait_on_result2()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(wait_on_result1(), wait_on_result2()))
    loop.close()
