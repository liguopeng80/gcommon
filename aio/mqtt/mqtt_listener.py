# -*- coding: utf-8 -*- 
# created: 2021-06-30
# creator: liguopeng@liguopeng.net

import asyncio
import json
import logging
import socket
import threading
from abc import abstractmethod
from datetime import datetime

import paho.mqtt.client as mqtt

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

    @staticmethod
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
        logger.debug("Socket opened")

        def cb():
            # logger.debug("Socket is readable, calling loop_read")
            client.loop_read()

        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        logger.debug("Socket closed")
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        """监听可写状态"""
        logger.debug("Watching socket for writability.")

        def cb():
            # logger.debug("Socket is writable, calling loop_write")
            client.loop_write()

        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        logger.debug("Stop watching socket for writability.")
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

        # asyncio loop
        self.loop = asyncio.get_running_loop()

        self.disconnected = self.loop.create_future()

    def send_message(self, topic, message, qos=0) -> mqtt.MQTTMessageInfo:
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False, separators=(",", ":"))

        if isinstance(message, str):
            message = message.encode(encoding="utf-8")

        info = self.client.publish(topic, message, qos=qos)
        return info

    def start(self) -> None:
        # 建立连接
        if self.config.enable_ssl:
            self.client.tls_set()

        aio_helper = AsyncioHelper(self.loop, self.client)

        self.client.connect(self.config.server_address, self.config.server_port, 60)
        self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)
        self.client.username_pw_set(self.config.username, self.config.password)

    async def stop(self):
        self.client.loop_forever()
        logger.info("Disconnected: {}".format(await self.disconnected))

    def on_subscribe_v5(self, client, userdata, mid, reasonCodes, properties):
        pass

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_connect(self, client, userdata, flags, rc):
        logger.info('Connected with result code: %s, msg: %s',
                    str(rc), mqtt.error_string(rc))

        if rc != mqtt.MQTT_ERR_SUCCESS:
            return

        # client.subscribe('robot/')
        assert client == self.client
        # self.client.subscribe("robot/+/topic/task_status")
        self.observer.on_mqtt_connected(client, userdata, flags, rc)

    def on_disconnect(self, client, userdata, rc):
        self.disconnected.set_result(rc)

    def subscribe(self, topic, qos=0, options=None, properties=None):
        result, mid = self.client.subscribe(topic, qos, options, properties)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error('cannot subscribe topic: %s, code: %s, msg: %s',
                         topic, result, mqtt.error_string(result))
            return False

        return True

    def unsubscribe(self, topic, properties=None):
        self.client.unsubscribe(topic, properties)

    @abstractmethod
    def on_message(self, client, userdata, message):
        logger.info(message.topic + " " + str(message.payload))
        self.observer.on_mqtt_message(client, userdata, message)
