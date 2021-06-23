# -*- coding: utf-8 -*- 
# created: 2021-06-17
# creator: liguopeng@liguopeng.net

"""基于 asyncio 封装的常用异步函数"""

import asyncio


def async_call_later(timeout, func, *args, **kwargs):
    """延迟调用

    :func: 同步或异步函数
    """
    async def _delay_call():
        await asyncio.sleep(timeout)
        result = func(*args, **kwargs)

        if asyncio.iscoroutine(result):
            await result

    loop = asyncio.get_running_loop()
    return loop.create_task(_delay_call())


async def maybe_async(func, *args, **kwargs):
    """异步调用一个函数，该函数可能是同步函数，也可能是异步函数"""
    result = func(*args, **kwargs)

    if asyncio.iscoroutine(result):
        result = await result

    return result

