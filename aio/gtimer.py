#!/usr/bin/python
# -*- coding: utf-8 -*- 
# created: 2014-12-02

"""Timer implemented by twisted."""

import asyncio

import logging
logger = logging.getLogger('timer')


class AsyncTimer(object):
    @staticmethod
    def start(seconds):
        d = Deferred()
        reactor.callLater(seconds, d.callback, None)
        return d

    @staticmethod
    async def wait(seconds):
        """ wait until interrupted by callback or timeout that will raise a CancelledError """
        d = Deferred()
        _delayed_call = reactor.callLater(seconds, timeout, d)
        d._gcommon_delayed_call = _delayed_call

        def _on_finished(result):
            logger.debug(">>> AsyncTimer _on_finished: %s, defer: %s", result, d)
            if _delayed_call.active():
                logger.debug("--- AsyncTimer.wait, job done! cancel timer.")
                _delayed_call.cancel()

            return result

        d.addBoth(_on_finished)

        return d

    @staticmethod
    def cancel_timer(d):
        d._gcommon_delayed_call.cancel()


class Timer(object):
    Not_Started = 0
    Started = 1
    Timed_Out = 2
    Cancelled = 3
    
    def __init__(self, seconds, timeout_handler, *args, **kwargs):
        self.status = self.Not_Started
        
        self.seconds = seconds

        self.timeout_handler = timeout_handler
        self._args = args
        self._kwargs = kwargs
        
        self._task = None
        
    async def start(self):
        if self.status != self.Not_Started:
            return None

        self.status = self.Started
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self.seconds)

        if self.status == self.Started:
            await self.timeout_handler(*self._args, **self._kwargs)

    def restart(self, seconds = 0):
        if seconds:
            self.seconds = seconds
            
        if self.status == self.Started:
            self.cancel()
            
        self.status = self.Not_Started
        self.start()
        
        return self
        
    def cancel(self):
        if self.status != self.Started:
            return
            
        self.status = self.Cancelled
        self._task.cancel()

