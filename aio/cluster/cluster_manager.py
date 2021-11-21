#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-05-06

"""应用服务器集群"""
import abc
import logging

logger = logging.getLogger('server')


class NodeAllocator(object):
    """根据请求的 key 分配节点"""
    @abc.abstractmethod
    def set_nodes(self, nodes):
        """初始化设置，增加服务节点"""
        pass

    @abc.abstractmethod
    def add_server_nodes(self, **nodes):
        """增加新的服务节点"""
        pass

    @abc.abstractmethod
    def del_server_nodes(self, **nodes):
        """删除服务节点"""
        pass

    @abc.abstractmethod
    def get_server(self, key):
        """根据请求的 key，返回对应的服务器信息"""
        pass


class ClusterManager(object):
    """"维护当前服务器进程所提供的服务实例对象，以及所依赖的外部服务节点。"""
    server = None
    controller = None

    @staticmethod
    def reg_app_server(server):
        ClusterManager.server = server
        ClusterManager.controller = server.controller


class NodeManager(object):
    """应用服务器集群节点管理"""
    _managers = {}

    @staticmethod
    def add_node_manager(service_name, allocator):
        """在全局注册表中，增加新的监控，监控新的服务"""
        manager = NodeManager(service_name, allocator)
        NodeManager._managers[service_name] = manager

        return manager

    @staticmethod
    def get_node_manager(service_name):
        return NodeManager._managers.get(service_name)

    def __init__(self, service_name, allocator: NodeAllocator):
        self.SERVICE_NAME = service_name

        # 节点分配器
        self._node_allocator = allocator

        # 是否已经启动对服务节点（健康状态）的监听
        self._watched = False

    def is_watched(self):
        return self._watched

    def set_watched(self, watched=True):
        self._watched = watched

    def set_server_nodes(self, nodes):
        """服务节点变更"""
        logger.info('service node changed - %s - nodes: %s', self.SERVICE_NAME, nodes)
        if not nodes:
            logger.critical('All service nodes DOWN - %s', self.SERVICE_NAME)

        self._node_allocator.set_nodes(nodes)

    def add_server_nodes(self, **nodes):
        """增加一个或者多个节点"""
        self._node_allocator.add_server_nodes(**nodes)

    def del_server_nodes(self, **nodes):
        """删除一个或者多个节点"""
        self._node_allocator.del_server_nodes(**nodes)

    def get_server(self, key):
        """获取给定 Key 所对应的服务器节点"""
        if not isinstance(key, str):
            key = str(key)

        return self._node_allocator.get_server(key)

