# -*- coding: utf-8 -*-
# created: 2021-06-30
# creator: liguopeng@liguopeng.net

import asyncio
import json
import logging
import socket
from abc import abstractmethod
from typing import Optional

import paho.mqtt.client as mqtt

from gcommon.aio import gasync
from gcommon.server.server_config import ServerConfig
from gcommon.utils import gtime

logger = logging.getLogger("mqtt")


class MqttConfig(ServerConfig):
    pass


class MqttObserverBase(object):
    mqtt_listener = None

    def set_mqtt_listener(self, listener):
        self.mqtt_listener = listener

    @abstractmethod
    def on_mqtt_connected(self, _client, _user_data, _flags, rc):
        logger.debug(_client)

    @abstractmethod
    def on_mqtt_disconnected(self, _client, _userdata, _rc):
        logger.debug(_client)

    @abstractmethod
    def on_mqtt_message(self, _client, _user_data, message):
        logger.debug(message.payload)

    def send_message(self, topic, message, qos=0) -> mqtt.MQTTMessageInfo:
        return self.mqtt_listener.send_message(topic, message, qos)


class AsyncioHelper:
    """绑定 mqtt client 的 I/O 事件到 loop 上"""

    def __init__(self, loop, client):
        self.loop = loop
        self.client = client

        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    def on_socket_open(self, client, userdata, sock):
        """监听可读状态"""
        logger.debug("socket opened")

        def cb():
            # logger.debug("Socket is readable, calling loop_read")
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        logger.critical("socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        """监听可写状态"""
        logger.debug("watching socket for writability.")

        def cb():
            logger.debug("socket is writable, calling loop_write")
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        logger.debug("stop watching socket for writability.")
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        logger.debug("misc_loop started")
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
        logger.debug("misc_loop finished")


class MqttListener(object):
    def __init__(self, config: MqttConfig, observer: MqttObserverBase):
        self.observer = observer

        self.config = config

        client_id = "rcs" + gtime.date_str_by_minute()
        self.client = mqtt.Client(client_id=client_id)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect

        if self.config.enable_ssl:
            self.client.tls_set()

        # pass
        self._subscribes = {}

        # asyncio loop
        self.loop = asyncio.get_running_loop()
        self._future_disconnected = None
        self._working = True

        self._aio_helper: Optional[AsyncioHelper] = None

    def send_message(self, topic, message, qos=0) -> mqtt.MQTTMessageInfo:
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

        self._future_disconnected = None
        gasync.async_call_later(1, self._connect)

    def start(self) -> None:
        # 建立连接
        logger.info("start mqtt service")
        self._working = True
        self._connect()

    def _connect(self):
        if not self._working:
            logger.warning("connect mqtt server on status: %s", self._working)
            return

        if self._future_disconnected:
            logger.warning("mqtt listener has already connected to server")
            return

        self._aio_helper = AsyncioHelper(self.loop, self.client)
        self._future_disconnected = self.loop.create_future()

        self.client.username_pw_set(self.config.username, self.config.password)
        self.client.connect(self.config.server_address, self.config.server_port, 60)
        self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    async def stop(self):
        logger.info("stop mqtt service")
        self.client.disconnect()
        logger.error("mqtt disconnected: {}".format(await self._future_disconnected))

    def on_subscribe_v5(self, client, userdata, mid, reasonCodes, properties):
        pass

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_connect(self, client, userdata, flags, rc):
        logger.info("Connected with result code: %s, msg: %s", str(rc), mqtt.error_string(rc))

        if rc == mqtt.MQTT_ERR_CONN_REFUSED:
            return
        elif rc != mqtt.MQTT_ERR_SUCCESS:
            return

        # client.subscribe('robot/')
        assert client == self.client
        # self.client.subscribe("robot/+/topic/task_status")
        self.observer.on_mqtt_connected(client, userdata, flags, rc)

        # 已经连上服务器，续订
        for topic, (qos, options, properties) in self._subscribes.items():
            self._do_subscribe(topic, qos, options, properties)

    def on_disconnect(self, client, userdata, rc):
        logger.error("disconnected with result code: %s, msg: %s", str(rc), mqtt.error_string(rc))

        if self._future_disconnected and (self._future_disconnected.done() or self._future_disconnected.cancelled()):
            self._future_disconnected.set_result(rc)
            self._future_disconnected = None

        self.observer.on_mqtt_disconnected(client, userdata, rc)
        if self._working:
            gasync.async_call_later(1, self.reconnect)

    def subscribe(self, topic, qos=0, options=None, properties=None):
        self._subscribes[topic] = (qos, options, properties)
        self._do_subscribe(topic, qos, options, properties)

    def _do_subscribe(self, topic, qos, options, properties):
        logger.debug("subscribe topic: %s", topic)
        result, mid = self.client.subscribe(topic, qos, options, properties)

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
        self.client.unsubscribe(topic, properties)

    @abstractmethod
    def on_message(self, client, userdata, message):
        logger.debug(message.topic + " " + str(message.payload))
        self.observer.on_mqtt_message(client, userdata, message)
