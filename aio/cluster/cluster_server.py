#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-05-04

import logging
import traceback

from gcommon.aio import gasync
from gcommon.aio.cluster import zk_helper
from gcommon.aio.cluster.cluster_config import ClusterConfig
from gcommon.aio.cluster.cluster_status import ServerStatus
from gcommon.aio.cluster.zk_service import ZookeeperService
from gcommon.aio.gserver import SimpleServer

logger = logging.getLogger('server')


class SimpleClusterServer(SimpleServer):
    STATUS_CONTROLLER_CLASS = None
    controller = None

    SERVICE_NAME = 'undefined'
    INSTANCE = 0

    DEFAULT_CONFIG = {}

    def __init__(self):
        SimpleServer.__init__(self)
        self._zk_service: ZookeeperService = None
        self._kazoo_client = None
        self._status = ServerStatus.STARTING

        self._working_root = zk_helper.get_path_to_working_service(self.service_name)
        self._alive_root = zk_helper.get_path_to_alive_service(self.service_name)

        self._cluster_config = ClusterConfig.parse(self.config.get("service.cluster"))
        self._event_zk_ready = gasync.AsyncEvent()

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

    async def _init_cluster(self):
        # init zookeeper client
        logger.debug('create zookeeper service')

        hosts = self.config.get('zookeeper.hosts')
        interval = self.config.get_int('zookeeper.connection_interval')

        zk_service = ZookeeperService(hosts, interval)
        self.controller.register_service(zk_service)

        zk_service.start()
        zk_service.subscribe(self._on_zk_service_status_changed)
        self._zk_service = zk_service

        # 等待 ZK 中集群状态就绪
        await self._event_zk_ready.wait()

    def _on_zk_service_status_changed(self, service):
        """Zookeeper 服务状态改变"""
        if service.is_good():
            """同步调用。在成功之前，服务器不能执行任何操作，因此不会有问题。"""
            logger.debug('creating server alive node on zookeeper')

            # 创建 service cluster 需要的 ZK 路径
            self._kazoo_client.ensure_path(self._working_root)
            self._kazoo_client.ensure_path(self._alive_root)

            # 监听服务节点变化
            self._kazoo_client.ChildrenWatch(self._working_root, self._on_cluster_nodes_changed)

    def _on_cluster_nodes_changed(self, nodes):
        """服务节点发生变化，检查自己是否需要提供服务"""
        if self._status.is_running():
            logger.debug(f"{self.service_name} cluster nodes changed, ignore...")
            return

        if not nodes:
            logger.debug(f"{self.service_name} cluster has no working nodes...")

        # 根据 "server-name.sequence" 的 sequence 排序
        nodes.sort(key=lambda x: x.split(".")[1], reverse=False)
        nodes = nodes[:self._cluster_config.max_working_nodes]
        node_names = [node.split(".") for node in nodes]
        node_names = [name for name, _sequence in node_names]

        if self.unique_server_name not in node_names:
            # 当前节点还需要继续排队
            logger.debug(f"{self.service_name} cluster nodes changed, "
                         f"but current service instance need wait for working ")
            return

        current_node_index = node_names.index(self.unique_server_name)
        current_node_path = nodes[current_node_index]

        # 解析现有节点的数据，选择第一个满足自己要求的索引
        values = [""] * len(nodes)
        for index, node_name in enumerate(nodes):
            node_path = f"{self._working_root}/{node_name}"
            node_data = zk_helper.get_node_data(self._kazoo_client, node_path)
            node_index = int(node_data)
            values[node_index] = node_names[index]

        # 服务在 cluster 中的索引，用于消息路由
        service_index_in_cluster = values.index("")
        zk_helper.update_node_data(self._kazoo_client, current_node_path,
                                   str(service_index_in_cluster))

        # 当前节点成功加入服务集群，通知应用服务器开始工作
        self._status = ServerStatus.RUNNING
        self._event_zk_ready.notify()

    async def _service_main(self):
        try:
            await gasync.maybe_async(self._init_cluster)
            await gasync.maybe_async(self.init_server)
            await gasync.maybe_async(self.start_server)
        except Exception as e:
            self.logger.fatal('server exception: %s', traceback.format_exc())
            gasync.stop_async_loop()
        else:
            self.logger.debug('--------- STARTED ---------')
