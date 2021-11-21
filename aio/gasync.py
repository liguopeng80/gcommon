# -*- coding: utf-8 -*- 
# created: 2021-06-17
# creator: liguopeng@liguopeng.net

"""基于 asyncio 封装的常用异步函数"""

import logging
import asyncio
import traceback

logger = logging.getLogger("asyncio")


class AsyncThreads(object):
    """管理当前进程中的事件循环，用于跨线程通信"""
    _main_loop = None
    _loops = {}

    @staticmethod
    def is_main_loop():
        """当前线程是否主线程（asyncio 主事件循环）"""
        try:
            running_loop = asyncio.get_running_loop()
        except:
            return False

        return running_loop == AsyncThreads._main_loop

    @staticmethod
    def get_main_loop():
        assert AsyncThreads._main_loop
        return AsyncThreads._main_loop

    @staticmethod
    def register_main_loop(main_loop=None):
        main_loop = main_loop or asyncio.get_event_loop()
        if AsyncThreads._main_loop == main_loop:
            return

        assert not AsyncThreads._main_loop
        AsyncThreads._main_loop = main_loop
        # AsyncIOEventLoop.register_event_loop("main", main_loop)
        return

    @staticmethod
    def register_thread_loop(name, loop):
        old_value = AsyncThreads._loops.get(name)
        assert not old_value or old_value == loop
        AsyncThreads._loops[name] = loop

    @staticmethod
    def get_thread_loop(name="main"):
        if not name or name == "main":
            return AsyncThreads.get_main_loop()

        return AsyncThreads._loops.get(name)


def _proxy_to_async_call(func, *args, **kwargs):
    """把未知调用封装成异步请求，忽略返回值。

    用于跨线程请求。
    """
    async_call_soon(func, *args, **kwargs)


def callback_run_in_main_thread(func):
    """decorator: 将回调发送到主线程（不在当前线程执行）"""
    def __func(*args, **kwargs):
        run_in_main_thread(func, *args, **kwargs)

    __func.__name__ = func.__name__
    return __func


def run_in_main_thread(func, *args, **kwargs):
    """在主事件循环中执行，不等待调用结果"""
    loop = AsyncThreads.get_main_loop()
    loop.call_soon_threadsafe(_proxy_to_async_call, func, *args, **kwargs)


def run_in_thread(loop_name, func, *args, **kwargs):
    loop = AsyncThreads.get_thread_loop(loop_name)
    loop.call_soon_threadsafe(_proxy_to_async_call, func, *args, **kwargs)


def async_call_later(timeout, func, *args, **kwargs):
    """延迟调用

    :func: 同步或异步函数
    """
    async def _delay_call():
        await asyncio.sleep(timeout)

        try:
            result = func(*args, **kwargs)

            if asyncio.iscoroutine(result):
                await result
        except:
            logger.error("async_call_later: func: %s, except: %s",
                         func, traceback.format_exc())
            raise

    loop = asyncio.get_running_loop()
    return loop.create_task(_delay_call())


def async_call_soon(func, *args, **kwargs):
    """延迟调用

    :func: 同步或异步函数
    """
    async def _delay_call():
        try:
            result = func(*args, **kwargs)

            if asyncio.iscoroutine(result):
                await result
        except:
            logger.error("async_call_soon: func: %s, except: %s",
                         func, traceback.format_exc())
            raise

    loop = asyncio.get_running_loop()
    return loop.create_task(_delay_call())


def call_when_running(func, *args, **kwargs):
    """当 loop 启动后调用

    :func: 同步或异步函数
    """
    async def _delay_call():
        try:
            result = func(*args, **kwargs)

            if asyncio.iscoroutine(result):
                await result
        except:
            logger.error("call_when_running: func: %s, except: %s",
                         func, traceback.format_exc())
            raise

    loop = asyncio.get_event_loop()
    loop.create_task(_delay_call())


def run_forever(*functions):
    loop = asyncio.get_event_loop()
    AsyncThreads.register_main_loop()

    for func in functions:
        call_when_running(func)

    loop.run_forever()


async def maybe_async(func, *args, **kwargs):
    """异步调用一个函数，该函数可能是同步函数，也可能是异步函数"""
    result = func(*args, **kwargs)

    if asyncio.iscoroutine(result):
        result = await result

    return result

