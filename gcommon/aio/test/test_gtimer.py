# -*- coding: utf-8 -*-
# created: 2021-07-04
# creator: liguopeng@liguopeng.net

import asyncio

from gcommon.aio.gtimer import AsyncTimer


def timeout_callback(f: asyncio.Future):
    print("timeout")
    f.set_result("Done")


async def test():
    f = asyncio.Future()
    AsyncTimer(timeout_callback, f).start(0.1)

    result = await f
    print(result)


if __name__ == "__main__":
    asyncio.run(test())
