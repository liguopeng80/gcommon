# -*- coding: utf-8 -*-
# created: 2015-05-13
# creator: liguopeng@liguopeng.net

"""集群服务的调用者，监控集群的工作状态，选择合适的节点发送请求"""


import logging
from functools import partial

from gcommon.aio import gasync
from gcommon.aio.cluster.allocator.mod_allocator import ModuloAllocator
from gcommon.aio.cluster.cluster_config import ClusterConfig
from gcommon.aio.cluster.cluster_manager import NodeManager
from gcommon.aio.cluster.zk_service import ZookeeperService

logger = logging.getLogger("zookeeper")


class ClusterClient(object):
    """Zookeeper 客户端，负责注册/删除/监控需要调用的集群服务"""

    def __init__(self, zk_service: ZookeeperService, cluster_config: ClusterConfig):
        self._under_working = False

        self._zk_service = zk_service
        self._kazoo_client = zk_service.kazoo_client

        self._cluster_config = cluster_config
        # self._working_root = zk_helper.get_path_to_working_service(self.service_name)
        # self._alive_root = zk_helper.get_path_to_alive_service(self.service_name)
        self._node_manager = NodeManager(self.service_name, ModuloAllocator(cluster_config))

    @property
    def service_name(self):
        return self._cluster_config.service_name

    def start(self):
        """初始化，注册回调关注服务状态"""
        logger.info("server register started")

        if not self._cluster_config.cluster_enabled:
            return

        self._zk_service.subscribe(self._on_zk_service_status_changed)

    def _on_zk_service_status_changed(self, service):
        """Zookeeper 服务状态改变"""
        assert service == self._zk_service

        if service.is_good():
            self._watch_service_nodes()

    def _watch_service_nodes(self):
        """同步调用。在该函数成功之前，客户端不能执行任何操作，因此不会有问题。"""
        logger.debug("creating server alive node on zookeeper")

        # 创建 service cluster 需要的 ZK 路径
        self._kazoo_client.ensure_path(self._cluster_config.working_root)
        self._kazoo_client.ensure_path(self._cluster_config.alive_root)

        # 监听服务节点变化
        self._kazoo_client.ChildrenWatch(self._cluster_config.working_root, self._on_cluster_nodes_changed)

    @gasync.callback_run_in_main_thread
    def _on_cluster_nodes_changed(self, nodes):
        """服务节点发生变化，可能要更新路由"""
        old_node_names = self._node_manager.allocator.node_names
        new_node_names = []
        new_nodes = {}

        # 获取所有的新节点（仅前面的节点提供服务）
        nodes.sort(key=lambda x: x.split(".")[1], reverse=False)
        available_nodes_count = min(self._cluster_config.max_working_nodes, len(nodes))
        for i in range(available_nodes_count):
            node_name, _zk_sequence = nodes[i].split(".")
            node_path = f"{self._cluster_config.working_root}/{nodes[i]}"

            new_node_names.append(node_name)
            new_nodes[node_name] = node_path

        # 删除退出服务的老节点
        for old_name in old_node_names:
            if old_name not in new_node_names:
                logger.info(f"service {self.service_name} - remove old node {old_name}")
                self._node_manager.allocator.del_server_nodes(old_name)

        # 增加新节点
        for new_name in new_node_names:
            if new_name not in old_node_names:
                logger.info(f"service {self.service_name} - add cluster node {new_name}")
                node_path = new_nodes[new_name]
                self._kazoo_client.DataWatch(node_path, partial(self._on_working_node_data_changed, new_name))
                self._node_manager.allocator.add_server_nodes((new_name, NodeManager.Invalid_Node_Index))

    @gasync.callback_run_in_main_thread
    def _on_working_node_data_changed(self, node_name, data, stat, event):
        if not data:
            logger.debug(f"service {self.service_name} - {node_name} has no data, waiting for it...")
            return

        if not self._node_manager.is_node_managed(node_name):
            logger.warning(f"service {self.service_name} - {node_name} is not managed any more.")
            return

        try:
            index = int(data)
        except:
            logger.fatal(f"service {self.service_name} - {node_name} updated invalid data: {data}!!")
            return

        logger.debug(f"service {self.service_name} - {node_name} enters working mode on index: {index}.")
        self._node_manager.allocator.update_node(node_name, index)
