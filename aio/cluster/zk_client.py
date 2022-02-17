#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-04-22

"""ZooKeeper 客户端"""

import logging
import threading
from queue import Queue

from kazoo.client import KazooClient
from kazoo.handlers.threading import KazooTimeoutError
from kazoo.protocol.states import KazooState, KeeperState

from gcommon.aio import gasync
from gcommon.utils.gnet import ConnectionStatus

logger = logging.getLogger("kazoo")


class ZookeeperObserver(object):
    ZK_Conn_Connecting = "CONNECTING"

    def __init__(self):
        self._client_manager = None
        self._kazoo_client = None

        self._conn_status = ConnectionStatus.Initialized
        self._zk_conn_status = self.ZK_Conn_Connecting

    def set_client_manager(self, client_manager):
        self._client_manager = client_manager
        self._kazoo_client = self._client_manager.kazoo_client

    def on_connection_failed(self, reason=None):
        """Client Manager 回调"""
        logger.error("cannot connect to zookeeper, reason: %s", reason)

        self._conn_status = ConnectionStatus.Closed
        self._zk_conn_status = KazooState.LOST

        gasync.run_in_main_thread(self._on_conn_failed)

    def _on_conn_opened(self):
        """连接打开或者恢复"""
        pass

    def _on_conn_lost(self):
        """会话断开"""
        pass

    def _on_conn_suspended(self):
        """连接断开，会话挂起，尝试恢复中"""
        pass

    def _on_conn_failed(self):
        """第一次连接失败，无法建立会话"""
        pass

    def on_connection_status_changed(self, state):
        """在 ZK 的独立线程中调用（禁止在主线程调用）"""
        logger.debug("connection status changed from %s to %s", self._zk_conn_status, state)
        self._zk_conn_status = state

        if state == KazooState.CONNECTED:
            if self._kazoo_client.client_state == KeeperState.CONNECTED_RO:
                logger.debug("Read only mode!")
            else:
                logger.debug("Read/Write mode!")

            self._conn_status = ConnectionStatus.Connected
            gasync.run_in_main_thread(self._on_conn_opened)

        elif state == KazooState.LOST:
            logger.debug("kazoo connection lost (client closed)")
            self._conn_status = ConnectionStatus.Closed
            gasync.run_in_main_thread(self._on_conn_lost)

        elif state == KazooState.SUSPENDED:
            logger.debug("kazoo connection suspended (maybe the server is gone)")
            self._conn_status = ConnectionStatus.Suspended
            gasync.run_in_main_thread(self._on_conn_suspended)


class _ZookeeperClientThread(threading.Thread):
    """运行 kazoo 客户端的专用线程。"""

    def __init__(self, client):
        threading.Thread.__init__(self, daemon=True)
        self._client = client

    def run(self):
        logger.info("enter kazoo thread")
        self._client.thread_main()
        logger.info("leave kazoo thread")


class ZookeeperClient(object):
    """Kazoo 客户端管理器，用于管理 zk connection 和跨线程通信。

    不处理任何实际业务。处理业务的是 ZookeeperService.
    """

    def __init__(self, observer, server_addr):
        self._observer = observer

        self._kazoo_client = KazooClient(hosts=server_addr)
        self._q_service_control = Queue()

        self._is_running = True
        self._thread = _ZookeeperClientThread(self)

    @property
    def kazoo_client(self):
        return self._kazoo_client

    def is_running(self):
        return self._is_running

    def send_control_message(self, message):
        """发送控制消息，控制消息必须在客户端的启动线程中处理"""
        self._q_service_control.put(message)

    def _process_service_control_message(self):
        """处理控制消息"""
        message = self._q_service_control.get()
        logger.debug("process control message: %s", message)

        if message == "stop":
            self._is_running = False
            self._kazoo_client.stop()

    def start(self):
        """启动独立线程运行 zookeeper 客户端 - 主线程调用"""
        assert gasync.AsyncThreads.is_main_loop()
        logger.info("start kazoo client")

        self._kazoo_client.add_listener(self._observer.on_connection_status_changed)
        self._thread.start()

    def stop(self):
        logger.info("stop kazoo client")
        self.send_control_message("stop")

    def wait(self):
        logger.info("wait kazoo client exiting")
        self._thread.join()
        logger.info("kazoo client stopped")

    def thread_main(self):
        """尝试连接服务器，如果多次连接失败则抛出超时错"""
        try:
            self._kazoo_client.start()
        except KazooTimeoutError as e:
            self._observer.on_connection_failed(e)
            return
        except Exception as e:
            self._observer.on_connection_failed(e)
            return

        while self.is_running():
            self._process_service_control_message()

    def create_lock(self, node_root, node_name):
        return KazooLock(self._kazoo_client, node_root, node_name)


class KazooLock(object):
    def __init__(self, client: KazooClient, node_root, node_name):
        self._kazoo_client = client

        self._node_root = node_root
        self._node_name = node_name
        self._node_path = f"{node_root}/{node_name}."
        self._full_path = ""
        self._locked = False

    async def acquire(self):
        self._kazoo_client.create(self._node_path, b"", makepath=True, ephemeral=True, sequence=True)
        event = gasync.AsyncEvent()

        @gasync.callback_run_in_main_thread
        def _on_lock_nodes_changed(nodes):
            if not nodes:
                return

            nodes.sort(key=lambda x: x.split(".")[1], reverse=False)
            name, _sequence = nodes[0].split(".")
            if name == self._node_name:
                self._full_path = f"{self._node_root}/{nodes[0]}"
                event.notify(True)

        self._kazoo_client.ChildrenWatch(self._node_root, _on_lock_nodes_changed)
        await event.wait()
        return self

    def release(self):
        try:
            self._kazoo_client.delete(self._full_path)
        except:
            logger.fatal("kazoo lock release error, %s", self._node_path)
            raise

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
