# -*- coding: utf-8 -*- 
# created: 2021-11-21
# creator: liguopeng@liguopeng.net
from gcommon.aio.cluster.cluster_manager import ClusterAllocationType
from gcommon.utils import gobject
from gcommon.utils.gjsonobj import JsonObject


class ClusterConfig(object):
    zk_hosts = ""
    service_name = ""

    cluster_enabled = False
    working_mode = ClusterAllocationType.modulo
    max_working_nodes = 1

    @staticmethod
    def parse(cluster_config: JsonObject):
        self = ClusterConfig()

        gobject.copy_attributes(
            cluster_config, self,
            "zk_hosts",
            "cluster_enabled",
            "service_name",
            "working_mode",
            "max_working_nodes"
        )

        return self
