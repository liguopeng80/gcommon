#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-05-04

import logging

from gcommon.aio.cluster import zk_helper
from gcommon.aio.cluster.zk_service import ZookeeperService
from gcommon.aio.gserver import SimpleServer

logger = logging.getLogger('server')


class SimpleClusterServer(SimpleServer):
    STATUS_CONTROLLER_CLASS = None
    controller = None

    SERVICE_NAME = 'undefined'
    INSTANCE = 0

    DEFAULT_CONFIG = {}

    def init_server(self):
        """初始化服务器"""
        pass

    def start_server(self):
        """启动服务器"""
        raise NotImplementedError('for sub-class')

    def _get_service_specific_confg(self):
        """服务器特定的配置参数"""
        return None

    def _load_cluster(self):
        if self._is_zookeeper_enabled_in_cfg() and self.STATUS_CONTROLLER_CLASS:
            # todo: load init status from config file
            self.controller = self.STATUS_CONTROLLER_CLASS(self)
            self.controller.subscribe(self._on_server_status_changed)

            self._cluster_enabled = True
        else:
            self.STATUS_CONTROLLER_CLASS = None
            self._cluster_enabled = False

    def _is_zookeeper_enabled(self):
        return self.STATUS_CONTROLLER_CLASS is not None

    def _is_zookeeper_enabled_in_cfg(self):
        return self.config.get_bool('service.zookeeper.enabled')

    def is_running(self):
        """服务是否正在运行"""
        if self._is_zookeeper_enabled():
            return self.controller.is_running()
        else:
            # 没有状态控制类的服务总是处于运行状态
            return True

    def _on_server_status_changed(self, _controller):
        """服务器状态改变（停止/运行）"""
        # raise NotImplementedError('for sub-class')
        pass

    def _init_cluster(self):
        # init zookeeper client
        logger.debug('create zookeeper service')

        hosts = self.config.get('zookeeper.hosts')
        interval = self.config.get_int('zookeeper.connection_interval')

        zk_service = ZookeeperService(hosts, interval)
        self.controller.register_service(zk_service)

        zk_service.start()
