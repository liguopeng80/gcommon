# -*- coding: utf-8 -*-
# created: 2021-11-22
# creator: liguopeng@liguopeng.net

import asyncio

from gcommon.aio import gasync

event = gasync.AsyncEvent()


def sync_call():
    print("sync")
    return "1"


def notify():
    event.notify("welcome")


async def test():
    gasync.async_call_later(2, notify)
    result = await event.wait()
    print(result)


if __name__ == "__main__":
    asyncio.run(test())
