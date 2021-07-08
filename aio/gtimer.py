#!/usr/bin/python
# -*- coding: utf-8 -*- 
# created: 2014-12-02

"""Timer implemented by twisted."""

import asyncio

import logging
from datetime import datetime

import typing

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
            return None

        self.seconds = self._calc_timeout(seconds, dt)

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
            # maybe_async
            self.timeout_handler(*self._args, **self._kwargs)

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

    def cancel(self):
        if self.status != self.Started:
            return

        self.status = self.Cancelled
        self._task.cancel()
