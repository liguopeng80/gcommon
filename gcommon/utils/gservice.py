# -*- coding: utf-8 -*-
#
# author: Guopeng Li
# created: 27 Aug 2008
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

_Stopped = 0
_Stopping = 1
_Starting = 2
_Started = 3


class ServiceStatus:
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
        # old_value, self._status = self._status, value
        self._status = value
        return self._status


class BaseServer:
    SERVICE_NAME = "undefined"
    IS_MULTI_THREAD = False
    INSTANCE = 0

    # Adding nosec since this fails bandit B104: Possible binding to all interfaces
    VERSION = "0.0.0.0"  # nosec

    DEFAULT_CONFIG = {}

    # @abc.abstractmethod
    # def start(self):
    #     pass

    # @abc.abstractmethod
    # def run(self):
    #     pass

    # @abc.abstractmethod
    # def on_failure(self, event):
    #     pass

    @property
    def is_server(self):
        return False

    @property
    def is_standalone(self):
        return False

    @property
    def is_testing(self):
        return False
