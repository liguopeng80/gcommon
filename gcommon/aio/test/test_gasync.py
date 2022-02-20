# -*- coding: utf-8 -*-
# created: 2021-06-22
# creator: liguopeng@liguopeng.net
import asyncio

from gcommon.aio.gasync import maybe_async


def sync_call():
    print("sync")
    return "1"


async def async_call():
    await asyncio.sleep(1)
    print("async")
    return "2"


async def test():
    r = await maybe_async(sync_call)
    print(r)

    r = await maybe_async(async_call)
    print(r)


if __name__ == "__main__":
    asyncio.run(test())
