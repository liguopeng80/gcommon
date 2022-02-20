# -*- coding: utf-8 -*-
# created: 2021-11-21
# creator: liguopeng@liguopeng.net
from functools import partial

from gcommon.aio import gasync
from gcommon.aio.cluster.cluster_client import ClusterClient
from gcommon.aio.cluster.cluster_config import ClusterConfig
from gcommon.aio.cluster.zk_service import ZookeeperService
from gcommon.utils import genv, gmain
from gcommon.utils.gglobal import Global


def main(cluster_config: ClusterConfig):
    zk_service = ZookeeperService(cluster_config.zk_hosts)
    zk_service.start()

    cluster_client = ClusterClient(zk_service, cluster_config)
    cluster_client.start()


if __name__ == "__main__":
    config_file = genv.get_relative_folder(__file__, "demo-cluster-client.yaml")
    genv.set_env(gmain.ENV_CONFIG_FILE, config_file)

    config = gmain.init_main(thread_logger=True)
    config.load_module_in_config_folder("demo-cluster-client")
    Global.set_config(config)

    module_config = config.get("demo-cluster-client")
    cluster_config = ClusterConfig.parse(module_config.zookeeper)

    gasync.run_forever(partial(main, cluster_config))
