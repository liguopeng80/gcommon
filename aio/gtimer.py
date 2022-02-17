#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2014-12-02

"""Timer implemented by asyncio."""

import asyncio
import logging
import traceback
from asyncio import Future
from datetime import datetime

from gcommon.aio import gasync
from gcommon.utils import gregister

logger = logging.getLogger("timer")


class AsyncWait(object):
    """等待异步事件发生，支持超时

    注意：如果事件在等待之前发生，则无法捕捉该事件。

    watch("event1")
    await wait("event1", 10)

    or

    watch_and_wait("event1", 10)
    """

    def __init__(self):
        self._commands = gregister.Registry("asyncio-register")

    def watch(self, key, timeout_seconds=0):
        future = Future()
        self._commands.register(key, future)
        logger.warning("future registered, key: %s", key)

    async def wait(self, key, timeout_seconds=0):
        future: Future = self._commands.get(
            key,
        )
        if not future:
            # 没有 watch, 当作 timeout 处理
            logger.warning("wait future which is not registered, key: %s", key)
            raise asyncio.TimeoutError("not registered")

        try:
            await asyncio.wait_for(future, timeout_seconds)
        except asyncio.TimeoutError:
            self._commands.unregister(key)
            raise

    async def watch_and_wait(self, key, timeout_seconds=0):
        future = Future()
        self._commands.register(key, future)
        logger.debug("future registered, key: %s", key)

        try:
            return await asyncio.wait_for(future, timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning("future timed out, key: %s", key)
            self._commands.unregister(key)
            raise

    def set_result(self, key, result=None):
        """事件结束，通知事件已经完成"""
        future: Future = self._commands.get(key)
        if not future:
            logger.warning("future is not registered, key: %s", key)
            return

        self._commands.unregister(key)
        if future.done() or future.cancelled():
            logger.warning(
                "future has been finished, key: %s, done: %s, cancelled: %s",
                key,
                future.done(),
                future.cancelled(),
            )
            return

        logger.debug("future notified, key: %s", key)
        future.set_result(result)

    def set_exception(self, key, result=None):
        """事件结束，通知事件已经完成"""
        future: Future = self._commands.get(key)

        if not future:
            logger.warning("future is not registered, key: %s", key)
            return

        self._commands.unregister(key)
        if future.done() or future.cancelled():
            logger.warning(
                "future has been finished, key: %s, done: %s, cancelled: %s",
                key,
                future.done(),
                future.cancelled(),
            )
            return

        logger.warning("future notified, key: %s", key)
        future.set_exception(result)


class AsyncTimer(object):
    Not_Started = 0
    Started = 1
    Timed_Out = 2
    Cancelled = 3

    def __init__(self, timeout_handler, *args, **kwargs):
        self.status = self.Not_Started

        self.seconds = 0
        self.timeout_handler = timeout_handler
        self._args = args
        self._kwargs = kwargs

        self._task = None

    def set_handler(self, handler, *args, **kwargs):
        self.timeout_handler = handler
        self._args = args
        self._kwargs = kwargs

    def start(self, *, seconds: float = 0, dt: datetime = None):
        if self.status != self.Not_Started:
            logger.error("cannot start timer %s", self)
            return None

        self.seconds = self._calc_timeout(seconds, dt)
        logger.debug("start timer (%s) for %s seconds", self, self.seconds)

        # 启动异步函数
        self.status = self.Started
        self._task = asyncio.ensure_future(self._job())

    @staticmethod
    def _calc_timeout(seconds: float, dt: datetime):
        if dt:
            seconds = (dt - datetime.now()).total_seconds()
            if seconds < 0:
                seconds = 0

        return seconds

    async def _job(self):
        await asyncio.sleep(self.seconds)
        if self.status == self.Started:
            self.status = self.Timed_Out
            # await self.timeout_handler(*self._args, **self._kwargs)
            try:
                await gasync.maybe_async(self.timeout_handler, *self._args, **self._kwargs)
            except:
                logger.error(
                    "timer handler error, timer: %s, exception: %s",
                    self,
                    traceback.format_exc(),
                )
                raise
            # self.timeout_handler(*self._args, **self._kwargs)

    def restart(self, seconds: int = 0, dt: datetime = None):
        # self.seconds = self._calc_timeout(seconds, dt)

        if self.status == self.Started:
            self.cancel()
        elif self.status == self.Timed_Out:
            # todo: 已经超时，怎么处理？
            pass

        self.status = self.Not_Started
        self.start(seconds=seconds, dt=dt)

        return self

    def cancel(self, reason=""):
        if reason:
            logger.debug("cancel timer (%s) for reason: %s", self, reason)

        if self.status != self.Started:
            return

        self.status = self.Cancelled
        self._task.cancel()
