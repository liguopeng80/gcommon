# -*- coding: utf-8 -*-
# created: 2021-11-23
# creator: liguopeng@liguopeng.net

from gcommon.aio.cluster.cluster_server import SimpleClusterServer
from gcommon.utils import genv, gmain


class DemoClusterServer(SimpleClusterServer):
    SERVICE_NAME = "guli-demo"
    INSTANCE = 0

    def start_server(self):
        self.logger.info("server started")
        pass


if __name__ == "__main__":
    config_file = genv.get_relative_folder(__file__, "demo-cluster-server.yaml")
    genv.set_env(gmain.ENV_CONFIG_FILE, config_file)
    DemoClusterServer.start()
