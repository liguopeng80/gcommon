# -*- coding: utf-8 -*-
# created: 2021-06-17
# creator: liguopeng@liguopeng.net

"""基于 asyncio 封装的常用异步函数"""

import asyncio
import logging
import time
import traceback
from asyncio import Future

logger = logging.getLogger("asyncio")


class AsyncTask(object):
    def __init__(self, task=None):
        self._async_task: Future = task

    def set_task(self, task=None):
        assert not self._async_task
        self._async_task = task

    def cancel(self):
        """取消正在执行的异步（下货）任务"""
        if self._async_task and not self._async_task.done():
            self._async_task.cancel()

        self._async_task = None


class AsyncEvent(object):
    """可以等待的事件对象"""

    def __init__(self, triggered=False, pulse_mode=False, auto_reset=True):
        self._triggered = triggered
        self._result = True

        self._pulse_mode = pulse_mode
        self._auto_reset = auto_reset

        self._waiters = []

    def _check_auto_reset(self):
        if self._auto_reset:
            self._triggered = False

    async def wait(self):
        """等待事件被激发，如果已经被激发，则直接返回"""
        if self._triggered:
            self._check_auto_reset()
            return self._result

        future = asyncio.Future()
        self._waiters.append(future)
        return await future

    def notify(self, result=True):
        """通知等待者。如果允许，保留事件的激发状态"""
        if not self._pulse_mode:
            self._triggered = True
            self._result = result

        if self._waiters:
            self._check_auto_reset()
            self.pulse(result)

    def pulse(self, result=True):
        """通知等待者。不改变事件的激发状态。"""
        for waiter in self._waiters:
            waiter.set_result(result)

        self._waiters = []

    def reset(self):
        """重置事件的激发状态"""
        self._triggered = False
        self._result = True


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
            logger.error("async_call_later: func: %s, except: %s", func, traceback.format_exc())
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
            logger.error("async_call_soon: func: %s, except: %s", func, traceback.format_exc())
            raise

    loop = asyncio.get_running_loop()
    return loop.create_task(_delay_call())


class RunningContext(object):
    """为需要互斥的操作提供上下文保护"""

    class ErrorContextAlreadyRunning(Exception):
        pass

    def __init__(self, name="", logger=None):
        self._is_running = False

        self._name = ""
        self._logger = logger

    @property
    def is_running(self):
        return self._is_running

    def run(self, func, *args, **kwargs):
        if self.is_running:
            return

        with self:
            func(*args, **kwargs)

    async def async_run(self, func, *args, **kwargs):
        if self.is_running:
            return

        with self:
            await async_call_soon(func, *args, **kwargs)

    def __enter__(self):
        if self._is_running:
            raise self.ErrorContextAlreadyRunning()

        if self._logger:
            self._logger.debug("enter context %s", self._name)

        self._is_running = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._logger:
            self._logger.debug("exit context %s", self._name)

        self._is_running = False

        if self._logger and exc_type:
            self._logger.error(
                "running context %s got error: %s, %s, %s",
                self._name,
                exc_type,
                exc_val,
                exc_tb,
            )


class AsyncRunningContext(RunningContext):
    def async_call(self, func, *args, **kwargs):
        async_call_soon(self.async_run, func, *args, **kwargs)


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
            logger.error("call_when_running: func: %s, except: %s", func, traceback.format_exc())
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


def stop_async_loop():
    """停止事件循环"""
    # todo: 判断当前线程是否存在运行中的事件循环
    loop = asyncio.get_event_loop()
    loop.stop()


async def async_wait_by_step(total, step):
    started = time.time()
    count = 0
    while True:
        now = time.time()
        if now - started < total:
            if count:
                await asyncio.sleep(step)

            yield count
            count += 1
