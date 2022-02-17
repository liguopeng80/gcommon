# -*- coding: utf-8 -*-
# created: 2021-07-30
# creator: liguopeng@liguopeng.net
import asyncio
import time

from gcommon.aio.kafka.gkafka import KafkaConfig, KafkaConsumer
from gcommon.utils.gmain import init_main


def callback(topic, event_id, event_time, content):
    print(topic, event_id, event_time, content)


async def test():
    init_main()
    config = KafkaConfig()

    config.group_id = "Demo-%s" % int(time.time())
    config.topics = ["my-topic"]
    config.bootstrap_servers = ["test.server.com:9092"]

    consumer = KafkaConsumer(config, callback)
    await consumer.consume_forever()


async def test_config():
    config = init_main()
    kafka_config = KafkaConfig.create(config.get("kafka"))
    consumer = KafkaConsumer(kafka_config, callback)
    await consumer.consume_forever()


if __name__ == "__main__":
    asyncio.run(test())
