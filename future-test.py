import asyncio


async def waiter(future):
    print("Waiting for value...")
    value = await future
    print("Got:", value)


async def setter(future):
    await asyncio.sleep(3)
    future.set_result("Hello World")


async def rubika_waiter(future_rubika_replay):
    print("Waiting for Replay...")
    msg = await future_rubika_replay
    print("Got_MSG:", msg)


async def rubika_setter(future_rubika_replay):
    await asyncio.sleep(3)
    future_rubika_replay.set_result("hello rubika")


async def main():
    future = asyncio.get_event_loop().create_future()
    future_rubika_replay = asyncio.get_event_loop().create_future()

    asyncio.create_task(waiter(future))
    asyncio.create_task(waiter(future_rubika_replay))
    asyncio.create_task(setter(future))
    asyncio.create_task(rubika_setter(future_rubika_replay))

    await asyncio.sleep(5)


asyncio.run(main())
