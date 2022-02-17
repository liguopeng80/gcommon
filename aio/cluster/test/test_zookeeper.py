# -*- coding: utf-8 -*-
# created: 2015-04-22
# creator: liguopeng@liguopeng.net

import logging
import threading

from kazoo.protocol.states import KazooState

from gcommon.aio import gasync
from gcommon.aio.cluster.zk_client import ZookeeperClient, ZookeeperObserver

format = "%(asctime)-15s %(levelname)-3s %(name)-8s %(message)s"
logging.basicConfig(format=format, level=logging.DEBUG)


lock = threading.Lock()
lock.acquire()


class MyObserver(ZookeeperObserver):
    def on_connection_failed(self):
        ZookeeperObserver.on_connection_failed(self)
        lock.release()

    def on_connection_status_changed(self, state):
        ZookeeperObserver.on_connection_status_changed(self, state)

        if state == KazooState.SUSPENDED:
            lock.release()


def main():
    hosts = "192.168.5.131:2181"
    observer = MyObserver()

    manager = ZookeeperClient(observer, hosts)
    observer.set_client_manager(manager)

    manager.start()

    # 等待事件
    lock.acquire()

    manager.stop()
    manager.wait()


if __name__ == "__main__":
    gasync.run_forever(main)
