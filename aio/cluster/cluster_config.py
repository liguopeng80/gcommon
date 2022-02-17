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

    working_root = ""
    alive_root = ""
    _lock_root = ""

    path_working_apps = ""
    path_alive_apps = ""
    path_app_locks = ""

    def get_lock_root(self, lock_name):
        return f"{self._lock_root}/{lock_name}"

    @staticmethod
    def parse(cluster_config: JsonObject, service_name=None):
        self = ClusterConfig()

        gobject.copy_attributes(
            cluster_config,
            self,
            "zk_hosts",
            "cluster_enabled",
            "service_name",
            "working_mode",
            "max_working_nodes",
            "path_working_apps",
            "path_alive_apps",
            "path_app_locks",
        )

        if service_name:
            self.service_name = service_name

        # self.working_root = zk_helper.get_path_to_working_service(self.service_name)
        # self.alive_root = zk_helper.get_path_to_alive_service(self.service_name)
        self.working_root = f"{self.path_working_apps}/{self.service_name}"
        self.alive_root = f"{self.path_alive_apps}/{self.service_name}"
        self._lock_root = f"{self.path_app_locks}/{self.service_name}"

        return self
