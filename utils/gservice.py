# -*- coding: utf-8 -*-
#
# author: Guopeng Li
# created: 27 Aug 2008


_Stopped = 0
_Stopping = 1
_Starting = 2
_Started = 3


class ServiceStatus(object):
    def __init__(self, enabled=False, status=_Stopped):
        self._enabled = enabled
        self._status = status

    def is_enabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def is_stopped(self):
        return self._status == _Stopped

    def start(self):
        self._status = _Starting

    def started(self):
        self._status = _Started

    def stop(self):
        self._status = _Stopped

    def stopped(self):
        self._status = _Stopped

    def get(self):
        return self._status

    def set(self, value):
        old_value, self._status = self._status, value
        return self._status

