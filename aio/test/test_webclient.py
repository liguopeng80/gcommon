# -*- coding: utf-8 -*-
# created: 2021-06-23
# creator: liguopeng@liguopeng.net
import asyncio

from gcommon.aio.restapi import get


async def test_get():
    body = await get("http://127.0.0.1:12580/v3/elevator/status?test=2")
    print(body)


if __name__ == "__main__":
    asyncio.run(test_get())
