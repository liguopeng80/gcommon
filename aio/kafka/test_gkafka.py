# -*- coding: utf-8 -*- 
# created: 2021-07-30
# creator: liguopeng@liguopeng.net
import asyncio
import time, logging

from gcommon.aio.kafka.gkafka import KafkaConfig, KafkaConsumer
from gcommon.utils.gmain import init_main


def callback(topic, event_id, event_time, content):
    print(topic, event_id, event_time, content)


async def test():
    init_main()
    config = KafkaConfig()

    config.group_id = "Demo-%s" % int(time.time())
    config.topics = ["task-status"]
    config.bootstrap_servers = ["kafka.demo.com:9092"]

    consumer = KafkaConsumer(config, callback)
    await consumer.consume_forever()


if __name__ == '__main__':
    asyncio.run(test())
