#!/usr/bin/python
# -*- coding: utf-8 -*- 
# created: 2014-12-02

"""Timer implemented by twisted."""

import asyncio

import logging
import traceback
from datetime import datetime

import typing

from gcommon.aio import gasync
from gcommon.aio.gasync import maybe_async

logger = logging.getLogger('timer')


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
                logger.error("timer handler error, timer: %s, exception: %s", self, traceback.format_exc())
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
