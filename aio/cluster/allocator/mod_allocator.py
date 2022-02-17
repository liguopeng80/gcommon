# -*- coding: utf-8 -*-
# created: 2021-11-21
# creator: liguopeng@liguopeng.net

"""基于整数取余的分配方式"""
from gcommon.aio.cluster.cluster_config import ClusterConfig
from gcommon.aio.cluster.cluster_manager import ClusterAllocationType, NodeAllocator


class NodeDesc(object):
    name = ""
    index = 0

    def __init__(self, index, name):
        self.index = index
        self.name = name


class ModuloAllocator(NodeAllocator):
    allocation_type = ClusterAllocationType.modulo

    def __init__(self, cluster_config: ClusterConfig):
        self._cluster_config = cluster_config
        self._server_nodes = []
        self._index_to_nodes = [""] * cluster_config.max_working_nodes

    @property
    def node_names(self):
        return [node.name for node in self._server_nodes]

    @property
    def node_indexes(self):
        return [node.index for node in self._server_nodes]

    def is_node_managed(self, node_name):
        return node_name in self.node_names

    def set_nodes(self, nodes):
        self._server_nodes = []
        for name, data in nodes:
            self.add_node(name, data)

    def add_server_nodes(self, *nodes):
        for name, data in nodes:
            self.add_node(name, data)

    def del_server_nodes(self, *nodes):
        for node_name in nodes:
            self.remove_node(node_name)

    def update_node(self, name, data=0):
        """增加一个新节点"""
        if name not in self.node_names:
            return

        index = self.node_names.index(name)
        self._server_nodes[index].index = data

        if data >= 0:
            self._index_to_nodes[data] = name

    def add_node(self, name, data=0):
        """增加一个新节点"""
        assert name not in self.node_names
        assert data < 0 or data not in self.node_indexes
        assert data < self._cluster_config.max_working_nodes

        node = NodeDesc(data, name)
        self._server_nodes.append(node)

        if data >= 0:
            self._index_to_nodes[data] = name

    def remove_node(self, name):
        """删除一个服务节点"""
        if name not in self.node_names:
            return

        index = self.node_names.index(name)
        node = self._server_nodes.pop(index)
        if node.index >= 0:
            self._index_to_nodes[node.index] = ""

    def get_server(self, key: int):
        """根据 key 选择服务节点"""
        # TODO: 增加临时备选方案
        index = key % self._cluster_config.max_working_nodes
        return self._index_to_nodes[index]
