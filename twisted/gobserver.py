#!/usr/bin/python
#
# author: Guopeng Li
# created: 27 Aug 2008

from twisted.internet.defer import Deferred


class Observer(object):
    def __init__(self, name=""):
        self._d = None
        self.name = name

    def register(self):
        assert self._d is None
        self._d = Deferred()

    def wait(self):
        assert self._d
        return self._d

    def notify(self, msg=None):
        if self._d:
            self._d.callback(msg)
            self._d = None

    def __nonzero__(self):
        return self._d is not None
