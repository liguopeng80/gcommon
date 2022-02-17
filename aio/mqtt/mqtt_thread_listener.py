# -*- coding: utf-8 -*-
# created: 2021-06-30
# creator: liguopeng@liguopeng.net

import asyncio
import logging
import threading
from abc import abstractmethod

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
        print(_client)

    @staticmethod
    def on_mqtt_message(self, _client, _user_data, message):
        print(message.payload)


class MqttListener(threading.Thread):
    def __init__(self, config: MqttConfig, observer: MqttObserverBase):
        threading.Thread.__init__(self)
        # daemon thread, 在按下 ctrl-c 之后程序可以退出
        self.daemon = True

        self.observer = observer

        self.config = config

        client_id = "rcs" + gtime.date_str_by_minute()
        self.client = mqtt.Client(client_id=client_id)

        # asyncio loop
        self.loop = asyncio.get_running_loop()

    def run(self) -> None:
        """注意：所有回调函数都在独立线程中执行"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe

        # 建立连接
        if self.config.enable_ssl:
            self.client.tls_set()

        self.client.connect(self.config.server_address, self.config.server_port, 60)
        self.client.username_pw_set(self.config.username, self.config.password)
        self.client.loop_forever()

    def on_subscribe_v5(self, client, userdata, mid, reasonCodes, properties):
        pass

    def on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def on_connect(self, client, userdata, flags, rc):
        logger.info("Connected with result code: %s, msg: %s", str(rc), mqtt.error_string(rc))

        if rc != mqtt.MQTT_ERR_SUCCESS:
            return

        # client.subscribe('robot/')
        assert client == self.client
        # self.client.subscribe("robot/+/topic/task_status")
        self.loop.call_soon_threadsafe(self.observer.on_mqtt_connected, client, userdata, flags, rc)

    def subscribe(self, topic, qos=0, options=None, properties=None):
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
        logger.info(message.topic + " " + str(message.payload))
        self.loop.call_soon_threadsafe(self.observer.on_mqtt_message, client, userdata, message)
