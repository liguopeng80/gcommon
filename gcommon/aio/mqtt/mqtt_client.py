#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# created: 2022-07-05
# creator: liguopeng@liguopeng.net

import abc
import asyncio
import logging

from paho.mqtt.client import MQTTMessageInfo

from gcommon.aio.mqtt.mqtt_listener import MqttConfig, MqttListener, MqttObserverBase
from gcommon.logger.log_util import log_callback
from gcommon.utils.gjsonobj import JsonObject


logger = logging.getLogger("gcommon.mqtt")


class MqttClient(MqttObserverBase):
    def __init__(self, config: JsonObject, client_id=""):
        self._mqtt_server_config = MqttConfig.load(config)
        self._mqtt_listener = MqttListener(self._mqtt_server_config, self, client_id)

        self.connected_future = asyncio.Future()

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
        pass

    @log_callback(logger)
    def on_mqtt_disconnected(self, client, userdata, rc):
        """和服务器之间的连接断开"""
        self.connected_future = None

    @log_callback(logger)
    def on_mqtt_connected(self, _client, _user_data, _flags, rc):
        """和 mqtt 服务器之间断开连接"""
        # self.mqtt_listener.subscribe()
        if not self.connected_future:
            self.connected_future = asyncio.Future()

        self.connected_future.set_result(True)

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
