import asyncio

async def foo():
    while True:
        print("foo")
        await asyncio.sleep(1)
        
async def bar():
    while True:
        print("bar")
        await asyncio.sleep(1)


async def main():
    # asyncio.create_task(foo())
    # asyncio.create_task(bar())
    # await asyncio.sleep(1)
    await asyncio.gather(foo(), bar())


print("Start Test")

asyncio.run(main())