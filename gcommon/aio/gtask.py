#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2014-12-02

"""Timer implemented by asyncio."""

import asyncio


class ScheduledTask(object):
    Not_Started = 0
    Started = 1
    Timed_Out = 2
    Cancelled = 3

    def __init__(self, seconds, timeout_handler, is_async=False, auto_repeat=False):
        self.status = self.Not_Started

        self.seconds = seconds

        self.timeout_handler = timeout_handler

        self._delayed_call = None
        self._is_async = is_async
        self._auto_repeat = auto_repeat

    def start(self):
        if self.status != self.Not_Started:
            return None

        self.status = self.Started

        loop = asyncio.get_event_loop()
        self._delayed_call = loop.call_later(self.seconds, self._on_timeout)  # @UndefinedVariable

        return self

    def restart(self, seconds=0):
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
        self._delayed_call.cancel()

    def _on_timeout(self):
        if self.status != self.Started:
            return

        self.status = self.Timed_Out

        if self._is_async:
            asyncio.get_event_loop().call_soon(self.timeout_handler)
        else:
            self.timeout_handler()
            if self._auto_repeat:
                self.start()


# Test Codes
if __name__ == "__main__":
    print("Done")
