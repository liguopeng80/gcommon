# -*- coding: utf-8 -*-
# created: 2015-05-12
# creator: liguopeng@liguopeng.net

"""网络相关的基础函数、基础类型"""

from enum import Enum


class ConnectionStatus(Enum):
    """所有支持的连接状态"""

    Initialized = "initialized"
    Connected = "connected"
    Closed = "closed"

    Connecting = "connecting"
    Reconnecting = "reconnecting"
    Suspended = "suspended"

    Connection_Failed = "connection_failed"
    Closing = "closing"

    @property
    def is_connecting(self):
        return self in (self.Connecting, self.Reconnecting)

    @property
    def is_connected(self):
        return self == self.Connected

    @property
    def is_closed(self):
        return self in (self.Connection_Failed, self.Closed, self.Initialized)

    @property
    def is_closing(self):
        return self == self.Closing

    @property
    def is_suspended(self):
        return self == self.Suspended
