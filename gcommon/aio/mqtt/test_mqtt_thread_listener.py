# -*- coding: utf-8 -*-
# created: 2021-06-30
# creator: liguopeng@liguopeng.net
import asyncio
import logging

from gcommon.aio.mqtt.mqtt_thread_listener import MqttConfig, MqttListener, MqttObserverBase
from gcommon.logger.glogger import init_basic_config
from gcommon.logger.log_util import log_callback

logger = logging.getLogger("iot")


class MyObserver(MqttObserverBase):
    @log_callback(logger)
    def on_mqtt_connected(self, client, userdata, flags, rc):
        self.mqtt_listener.subscribe("guli/test")

    @log_callback(logger)
    def on_mqtt_message(self, client, userdata, message):
        print(message.timestamp)


if __name__ == "__main__":
    init_basic_config()

    config = MqttConfig()

    config.server_port = 1883
    config.server_address = "mqtt.demo.com.cn"
    config.username = "demo"
    config.password = "demo"

    async def start_mqtt():
        await asyncio.sleep(0.01)
        observer = MyObserver()

        listener = MqttListener(config, observer)
        observer.set_mqtt_listener(listener)

        listener.start()

    loop = asyncio.get_event_loop()

    loop.create_task(start_mqtt())
    loop.run_forever()
