# -*- coding: utf-8 -*-
# created: 2021-07-04
# creator: liguopeng@liguopeng.net

import asyncio

from gcommon.aio.gtimer import AsyncTimer


def timeout_callback(f: asyncio.Future):
    print("timeout")
    f.set_exception(RuntimeError("Timeout"))


async def test():
    f = asyncio.Future()
    AsyncTimer(timeout_callback, f).start(seconds=0.1)

    try:
        result = await f
    except Exception as e:
        print("exception: ", e)
    else:
        print(result)


if __name__ == "__main__":
    asyncio.run(test())
