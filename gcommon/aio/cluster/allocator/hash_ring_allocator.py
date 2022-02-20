# -*- coding: utf-8 -*-
# created: 2021-11-19
# creator: liguopeng@liguopeng.net

"""基于一致性哈希的分配方式"""


from uhashring import HashRing

from gcommon.aio.cluster.cluster_manager import ClusterAllocationType, NodeAllocator


class HashRingAllocator(NodeAllocator):
    allocation_type = ClusterAllocationType.hash_ring

    def __init__(self):
        self._server_nodes = set()
        self._server_ring = HashRing(self._server_nodes)

    def set_nodes(self, nodes):
        self._server_nodes = set(nodes)
        self._server_ring = HashRing(self._server_nodes)

    def add_server_nodes(self, *nodes):
        """增加一个或者多个节点"""
        self._server_nodes.update(set(nodes))
        self._server_ring = HashRing(self._server_nodes)

    def del_server_nodes(self, *nodes):
        """删除一个或者多个节点"""
        self._server_nodes -= nodes
        self._server_ring = HashRing(self._server_nodes)

    def get_server(self, key):
        """获取给定 Key 所对应的服务器节点"""
        if not isinstance(key, str):
            key = str(key)

        return self._server_ring.get_node(key)
