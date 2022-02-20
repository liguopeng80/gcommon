#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-05-05

"""应用服务器所以来的外部服务"""

import logging
from enum import Enum

from gcommon.utils.gobserver import SimpleObservableSubject

logger = logging.getLogger("cluster")


class ExternalServiceLevel(Enum):
    Trivial = "trivial"
    Crucial = "crucial"

    def is_crucial(self):
        return self == self.Crucial


class ExternalServiceStatus(Enum):
    Good = "good"
    Bad = "bad"

    def is_good(self):
        return self == self.Good

    def is_bad(self):
        return not self.is_good()


class ExternalServiceIssue(object):
    """服务器运行时所遭遇的重要故障 - 仅用于描述服务的故障类型

    1. 故障发生时，服务器必须停止处理客户端请求
    2. 故障解决后，服务器才能继续对外提供服务
    """

    Service_Starting = "starting"  # Not a real error

    Err_Desc_Cannot_Be_Reached = "cannot-reach"
    Err_Desc_Unexpected_Exception = "unexpected-exception"

    def __init__(self, name, desc):
        self.name = name
        self.desc = desc

    def __str__(self):
        return "%s, %s" % (self.name, self.desc)


class ExternalService(SimpleObservableSubject):
    """服务器运行所依赖的外部服务，用来管理服务状态"""

    def __init__(self, name, level=ExternalServiceLevel.Crucial):
        SimpleObservableSubject.__init__(self)

        self.name = name

        self._level: ExternalServiceLevel = level
        self._status: ExternalServiceStatus = ExternalServiceStatus.Bad
        self._issue: ExternalServiceIssue = None

    def start(self):
        raise NotImplementedError("for-sub-class")

    def is_good(self):
        return self._status.is_good()

    def is_bad(self):
        return not self.is_good()

    def is_crucial(self):
        return self._level.is_crucial()

    def enable_service(self):
        """服务状态从不可用变为可用"""
        logger.info("external service %s enabled...", self.name)

        self._status = ExternalServiceStatus.Good
        self._issue = None

        self.notify_observers()

    def disable_service(self, issue=None):
        """服务器状态从可用变为不可用"""
        logger.info("external service %s disabled!!!", self.name)

        self._status = ExternalServiceStatus.Bad
        self._issue = issue

        self.notify_observers()

    def start_service(self):
        pass

    def __str__(self):
        desc = "%s-%s-%s" % (self.name, self._status.name, self._level.name)

        if self._issue:
            desc += "(%s)" % self._issue

        return desc
