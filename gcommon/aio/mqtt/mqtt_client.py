#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: 2022-07-05
# creator: liguopeng@liguopeng.net
"""Mqtt Client - Auto connection and manage subscriptions"""
import abc
import asyncio
import logging

from paho.mqtt.client import MQTTMessageInfo

from gcommon.aio.mqtt.mqtt_listener import MqttConfig
from gcommon.aio.mqtt.mqtt_listener import MqttListener
from gcommon.aio.mqtt.mqtt_listener import MqttObserverBase
from gcommon.logger.log_util import log_callback
from gcommon.utils.gjsonobj import JsonObject


logger = logging.getLogger("gcommon.mqtt")


class MqttClient(MqttObserverBase):
    """Mqtt Client - manage connection, subscriptions and message callback"""

    def __init__(self, config: JsonObject, client_id=""):
        self._mqtt_server_config = MqttConfig.load(config)
        self._mqtt_listener = MqttListener(self._mqtt_server_config, self, client_id)

        self.connected_future = asyncio.Future()
        self._is_connected = False

    def will_set(self, topic, payload=None, qos=0, retain=False):
        """设置 will message，必须在 connect 之前调用"""
        self._mqtt_listener.client.will_set(topic, payload, qos, retain)

    def start(self):
        """连接到服务器并启动监听"""
        logger.debug("connect to %s", self._mqtt_server_config.server_address)
        self._mqtt_listener.start()

    # @log_callback(logger)
    def on_mqtt_message(self, _client, _user_data, message):
        """收到 mqtt 消息，解码并且向应用层分发"""
        payload = JsonObject.loads(message.payload.decode("utf-8"))
        self._process_mqtt_message(message.topic, message.timestamp, payload)

    @abc.abstractmethod
    def _process_mqtt_message(self, topic, timestamp, payload: JsonObject):
        """处理 mqtt 消息，由派生类继承并调用"""

    @property
    def is_connected(self):
        """Is the connection is established"""
        return self._is_connected

    @log_callback(logger)
    def on_mqtt_disconnected(self, client, userdata, rc):
        """和服务器之间的连接断开"""
        self._is_connected = False
        self.connected_future = None
        self._on_disconnected()

    @log_callback(logger)
    def on_mqtt_connected(self, _client, _user_data, _flags, rc):
        """和 mqtt 服务器之间断开连接"""
        # self.mqtt_listener.subscribe()
        self._is_connected = True
        if not self.connected_future:
            self.connected_future = asyncio.Future()

        self.connected_future.set_result(True)
        self._on_connected()

    def _on_disconnected(self):
        pass

    def _on_connected(self):
        pass

    async def wait_for_connected(self):
        """等待 mqtt 连接到服务器"""
        if not self.connected_future:
            self.connected_future = asyncio.Future()

        return await self.connected_future

    def _send_message(self, topic, message, qos=0) -> MQTTMessageInfo:
        return self._mqtt_listener.send_message(topic, message, qos)

    def _subscribe(self, topic):
        """订阅"""
        self._mqtt_listener.subscribe(topic)

    def _unsubscribe(self, topic):
        """取消订阅"""
        self._mqtt_listener.subscribe(topic)
