#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-04-29

import logging
import threading
import time

from kazoo.protocol.states import KazooState, KeeperState

from gcommon.aio import gasync
from gcommon.aio.cluster.zk_client import ZookeeperClient, ZookeeperObserver
from gcommon.utils.gmain import init_main

formatter = "%(asctime)-15s %(levelname)-3s %(name)-8s %(message)s"
logging.basicConfig(format=formatter, level=logging.DEBUG)

logger = logging.getLogger()


PATH = "/test/guli/favorite"
APP_ROOT = "/test/guli/app"
APP_PATH = "/test/guli/app/gatekeeper"


class MyObserver(ZookeeperObserver):
    def __init__(self):
        super(MyObserver, self).__init__()
        self.connected = False

    def on_connection_failed(self, reason=None):
        ZookeeperObserver.on_connection_failed(self)
        gasync.run_in_main_thread(self._on_conn_failed)

    def on_connection_status_changed(self, state):
        """示例代码，演示如何捕获和处理连接状态变化事件。"""
        logger.debug("watch func called in thread: %s", threading.currentThread())
        if state == KazooState.CONNECTED and not self.connected:
            self.connected = True
            gasync.run_in_main_thread(self._on_conn_opened)
            if self._kazoo_client.client_state == KeeperState.CONNECTED_RO:
                logger.debug("Read only mode!")
            else:
                logger.debug("Read/Write mode!")
        elif state == KazooState.LOST:
            self.connected = False
            gasync.run_in_main_thread(self._on_conn_lost)
            logger.debug("kazoo connection lost (client closed)")
        elif state == KazooState.SUSPENDED:
            gasync.run_in_main_thread(self._on_conn_suspended)
            logger.debug("kazoo connection suspended (maybe the server is gone)")

    @gasync.callback_run_in_main_thread
    def on_children_changed(self, children):
        logger.debug("children changed - %s", children)

    @gasync.callback_run_in_main_thread
    def on_data_changed(self, data, stat, event):
        logger.debug("data changed - version: %s, data: %s" % (stat.version, data.decode("utf-8")))

    def _on_conn_lost(self):
        pass

    def _on_conn_opened(self):
        self._kazoo_client.ensure_path(PATH)
        self._kazoo_client.ChildrenWatch(PATH, self.on_children_changed)
        self._kazoo_client.DataWatch(PATH, self.on_data_changed)

        data_str = "hehe-%s" % time.time()
        data = data_str.encode("utf-8")

        # self._kazoo_client.delete(APP_PATH)
        self._kazoo_client.ensure_path(APP_ROOT)

        self._kazoo_client.ChildrenWatch(APP_ROOT, self.on_app_children_changed)
        self._kazoo_client.DataWatch(APP_ROOT, self.on_app_data_changed)

        for i in range(2):
            node_path = f"{APP_PATH}/rcs{data_str}."
            node_path = f"{APP_PATH}{int(time.time()*1000)}."
            self._kazoo_client.create(node_path, data, ephemeral=True, sequence=True)
            time.sleep(0.1)

        # reactor.callLater(5, self._gen_test_data)

    @gasync.callback_run_in_main_thread
    def on_app_children_changed(self, children):
        logger.debug("-- app children changed - %s", children)

    @gasync.callback_run_in_main_thread
    def on_app_data_changed(self, data, stat, event):
        if not data and not stat:
            logger.debug("-- app data changed without data")
            return

        logger.debug("-- app data changed - version: %s, data: %s" % (stat.version, data.decode("utf-8")))

    def _gen_test_data(self):
        # path = PATH + '/' + str(time.time())
        # self._kazoo_client.create(path, b"a value")
        self._kazoo_client.set(PATH, "wahaha-%s" % time.time())
        gasync.async_call_later(2, self._gen_test_data)

    def _on_conn_suspended(self):
        pass

    def _on_conn_failed(self):
        pass

    def start(self):
        self._client_manager.start()

    def stop(self):
        self._client_manager.stop()
        self._client_manager.wait()


if __name__ == "__main__":
    init_main(thread_logger=True)

    hosts = "192.168.5.131:2181"
    observer = MyObserver()

    manager = ZookeeperClient(observer, hosts)
    observer.set_client_manager(manager)

    gasync.run_forever(observer.start)
