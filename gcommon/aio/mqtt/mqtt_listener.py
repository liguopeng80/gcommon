# -*- coding: utf-8 -*-
# created: 2021-06-30
# creator: liguopeng@liguopeng.net
"""MQTT 客户端，保持和 mqtt server 之间的长连接，实现自动重连、自动订阅。

缺点：
1. 需要监听和检查 mqtt 的连接状态；
2. 订阅可能会失败，但是目前没有检查和处理这种错误；
3. 消息发送也可能失败，目前也没有处理这种错误，需要应用层进行容错处理；
"""
import asyncio
import json
import logging
import socket
import traceback
from abc import ABC
from abc import abstractmethod
from typing import Optional

import paho.mqtt.client as mqtt

from gcommon.aio import gasync
from gcommon.server.server_config import ServerConfig
from gcommon.utils import gtime

logger = logging.getLogger("gcommon.mqtt")


class MqttConfig(ServerConfig):
    """MQTT 服务器配置"""

    client_cert = None
    client_key = None
    client_key_password = None
    server_ca_cert = None

    def _load_extra_config(self, config):
        """派生类自定义的配置属性"""
        self.client_cert = config.client_cert
        self.client_key = config.client_key
        self.client_key_password = config.client_key_password
        self.server_ca_cert = config.server_ca_cert


class MqttObserverBase:
    """监听 mqtt 状态变化（建立连接、断开连接、收到消息）"""

    @abstractmethod
    def on_mqtt_connected(self, _client, _user_data, _flags, rc):
        """回调：MQTT 建立连接"""

    @abstractmethod
    def on_mqtt_disconnected(self, _client, _userdata, _rc):
        """回调：MQTT 断开连接"""

    @abstractmethod
    def on_mqtt_message(self, _client, _user_data, message):
        """回调：收到 mqtt 订阅消息"""


class MqttObserver(MqttObserverBase, ABC):
    """订阅 MQTT 状态变化，和 base 相比增加了 send_message 功能。"""

    _mqtt_listener = None

    def set_mqtt_listener(self, listener):
        """设置 mqtt listener，即被封状态的、真正的 mqtt client 对象"""
        self._mqtt_listener = listener

    def send_message(self, topic, message, qos=0) -> mqtt.MQTTMessageInfo:
        """发送 mqtt 消息，可以使用返回的 MQTTMessageInfo 对象判断消息是否发送成功"""
        return self._mqtt_listener.send_message(topic, message, qos)


class _AsyncioHelper:
    """实现 mqtt 客户端读写事件异步化

    原理：绑定 mqtt client 的 I/O 事件到 asyncio 的事件循环上。
    """

    def __init__(self, loop, client):
        self.loop = loop
        self.client = client

        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write
        self.misc = None

    def on_socket_open(self, client, userdata, sock):
        """连接建立，开始监听可读状态"""
        logger.debug("socket opened")

        def cb():
            # logger.debug("Socket is readable, calling loop_read")
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        """连接关闭，从 asyncio loop 中删除 reader"""
        logger.critical("socket closed")
        self.loop.remove_reader(sock)

        if self.misc:
            self.misc.cancel()
            self.misc = None

    def on_socket_register_write(self, client, userdata, sock):
        """监听可写状态"""
        logger.debug("watching socket for writability.")

        def cb():
            logger.debug("socket is writable, calling loop_write")
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        """取消写操作"""
        logger.debug("stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        """在连接保持期间循环执行，处理（发送）心跳等需要定时检查的事件"""
        logger.debug("misc_loop started")

        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break

        logger.debug("misc_loop finished")


class MqttListener:
    """持有 MQTT client 对象，监听 mqtt 状态变化和订阅消息。

    调用者通过注册 observer 对象接受 mqtt 事件通知。
    """

    # pylint: disable=too-many-instance-attributes,too-many-arguments

    reconnect_interval = 1

    def __init__(self, config: MqttConfig, observer: MqttObserverBase, client_id=""):
        self.observer = observer
        self.config = config

        if not client_id:
            client_id = f"gcommon-{gtime.local_time_str()}"

        self.client = mqtt.Client(client_id=client_id)
        self._init_mqtt_client()

        if self.config.enable_ssl:
            if config.client_cert and config.client_key:
                self.client.tls_set(
                    certfile=config.client_cert,
                    keyfile=config.client_key,
                    keyfile_password=config.client_key_password,
                    ca_certs=config.server_ca_cert,
                )
            else:
                self.client.tls_set(ca_certs=config.server_ca_cert)

        # pass
        self._subscribes = {}

        # asyncio loop
        self._loop = asyncio.get_running_loop()
        # 用于等待 mqtt 连接断开的 future 对象
        self._future_disconnected = None
        # 是否需要持续重连
        self._working = True

        self._aio_helper: Optional[_AsyncioHelper] = None

    def _init_mqtt_client(self):
        """初始化 mqtt client 的回调函数"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect

    def send_message(self, topic, message, qos=0) -> mqtt.MQTTMessageInfo:
        """发送 mqtt 消息。

        - 如果 message 类型是 dict，则对 dict 进行 json 序列化。
        - 如果 message 类型是字符串，则对 message 进行 utf-8 编码后发送。
        """
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False, separators=(",", ":"))

        if isinstance(message, str):
            message = message.encode(encoding="utf-8")

        info = self.client.publish(topic, message, qos=qos)
        return info

    def reconnect(self):
        """掉线重连"""
        logger.debug("reconnect mqtt server on status: %s", self._working)
        if not self._working:
            return

        logger.error("reconnecting to mqtt server")

        if self._future_disconnected and not self._future_disconnected.done():
            logger.warning("mqtt listener has already connected to server")
            return

        gasync.async_call_later(self.reconnect_interval, self._connect)

    def start(self) -> None:
        """建立连接，如果连接失败则自动尝试重连"""
        logger.info("start mqtt service")
        self._working = True
        self._connect()

    def _connect(self):
        """执行连接操作，失败后自动重连"""
        if not self._working:
            logger.warning("connect mqtt server on status: %s", self._working)
            return

        if self._future_disconnected and not self._future_disconnected.done():
            logger.warning("mqtt listener has already connected to server")
            return

        # 创建 future 对象，标记 mqtt 客户端正在连接或已经连上
        self._future_disconnected = self._loop.create_future()

        self._aio_helper = _AsyncioHelper(self._loop, self.client)
        self.client.username_pw_set(self.config.username, self.config.password)

        try:
            self.client.connect(self.config.server_address, self.config.server_port, 60)
        except:  # noqa: E722 - bare except
            # 在连接过程中发生异常，未能启动连接尝试。需要清理连接状态，并在允许的时候重试。
            logging.warning("cannot connect to mqtt server, exception: %s", traceback.format_exc())

            self._future_disconnected = None
            self.reconnect()
            return

        self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    async def stop(self):
        """关闭连接，并等待关闭动作结束"""
        logger.info("stop mqtt service")

        self._working = False

        if self._future_disconnected:
            self.client.disconnect()

            result = await self._future_disconnected
            self._future_disconnected = None

            logger.error("mqtt disconnected: %s", result)

    def on_subscribe_v5(self, client, userdata, mid, reasonCodes, properties):
        """订阅消息结束，可能成功或失败"""

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅消息成功"""

    def on_connect(self, client, userdata, flags, rc):
        """连接服务器成功"""
        logger.info("Connected with result code: %s, msg: %s", str(rc), mqtt.error_string(rc))

        if rc == mqtt.MQTT_ERR_CONN_REFUSED:
            return

        if rc != mqtt.MQTT_ERR_SUCCESS:
            return

        # client.subscribe('robot/')
        assert client == self.client
        # self.client.subscribe("robot/+/topic/task_status")
        self.observer.on_mqtt_connected(client, userdata, flags, rc)

        # 已经连上服务器，续订
        for topic, (qos, options, properties) in self._subscribes.items():
            self._do_subscribe(topic, qos, options, properties)

    def on_disconnect(self, client, userdata, rc):
        """和 mqtt 服务器之间的连接断开。

        如果没有停止工作，则自动重连。
        """
        logger.error("disconnected with result code: %s, msg: %s", str(rc), mqtt.error_string(rc))

        if self._future_disconnected:
            if self._future_disconnected.done() or self._future_disconnected.cancelled():
                # 连接已经关闭？？
                pass
            else:
                # 设置连接关闭的原因
                self._future_disconnected.set_result(rc)

        self.observer.on_mqtt_disconnected(client, userdata, rc)
        if self._working:
            self._future_disconnected = None
            gasync.async_call_later(self.reconnect_interval, self.reconnect)

    def subscribe(self, topic, qos=0, options=None, properties=None):
        """订阅 topic。

        无论客户端是否连接成功都可以发送该请求。客户端短线重连后不需要重复发送。
        todo: 未必能够订阅成功...
        """
        self._subscribes[topic] = (qos, options, properties)
        self._do_subscribe(topic, qos, options, properties)

    def _do_subscribe(self, topic, qos, options, properties):
        """发送执行订阅请求"""
        logger.debug("subscribe topic: %s", topic)
        result, _mid = self.client.subscribe(topic, qos, options, properties)

        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error(
                "cannot subscribe topic: %s, code: %s, msg: %s",
                topic,
                result,
                mqtt.error_string(result),
            )
            return False

        return True

    def unsubscribe(self, topic, properties=None):
        """取消 topic 订阅"""
        self.client.unsubscribe(topic, properties)

    def on_message(self, client, userdata, message):
        """收到 mqtt 消息，通知 observer"""
        logger.debug("on mqtt message, topic: %s, payload: %s", message.topic, str(message.payload))
        self.observer.on_mqtt_message(client, userdata, message)
