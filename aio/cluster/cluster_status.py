#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-05-04

"""服务器状态监控和管理"""
import logging
from enum import Enum

from gcommon.aio import gasync
from gcommon.utils.gerrors import format_exception_stack
from gcommon.utils.gobserver import SimpleObservableSubject

logger = logging.getLogger('server')


class ServerStatus(Enum):
    """服务器的运行时状态"""
    UNKNOWN = "unknown"

    WAITING = "waiting"                # 等待外部依赖
    STARTING = "starting"               # 正在启动
    RUNNING = "running"                # 正在运行
    STOPPING = "stopping"               # 正在关闭（优雅的关闭）
    STOPPED = "stopped"                # 服务已经停止

    ALL_STATUS = (WAITING, STARTING, RUNNING, STOPPING, STOPPED)
    ACTIVE_STATUS = (WAITING, STARTING, RUNNING)
    STANDBY_STATUS = (STOPPING, STOPPED)

    def is_waiting(self):
        return self.status == self.WAITING

    def is_starting(self):
        return self.status == self.STARTING

    def is_running(self):
        return self.status == self.RUNNING

    def is_stopped(self):
        return self.status == self.STOPPED

    def is_stopping(self):
        return self.status == self.STOPPING

    def is_active(self):
        return self.status in self.ACTIVE_STATUS

    def is_standby(self):
        return self.status in self.STANDBY_STATUS

    def change_status(self, new_status, desc=''):
        self.status = new_status
        self.status_desc = desc

    def __str__(self):
        return str(self.status)


class ServerEvent(object):
    # 服务器转换为活动状态
    Event_Active = 1
    # 服务器转换为备用状态
    Event_Stop = 2

    # 外部服务变为不可用状态
    Event_External_Service_Changed = 10
    # 外部依赖就绪，启动
    Event_External_Service_Ready = 11

    # 服务器启动
    Event_Start_Failed = 20     # 启动失败
    Event_Started = 21          # 启动成功

    # 停止
    Event_Stopped = 31

