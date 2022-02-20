# -*- coding: utf-8 -*-
# created: 2021-08-02
# creator: liguopeng@liguopeng.net

"""
https://aiokafka.readthedocs.io/en/stable/
"""

import asyncio

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


async def consume():
    consumer = AIOKafkaConsumer(
        "my_topic",
        "my_other_topic",
        bootstrap_servers="localhost:9092",
        group_id="my-group",
    )
    # Get cluster layout and join group `my-group`
    await consumer.start()
    try:
        # Consume messages
        async for msg in consumer:
            print(
                "consumed: ",
                msg.topic,
                msg.partition,
                msg.offset,
                msg.key,
                msg.value,
                msg.timestamp,
            )
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()


async def send_one():
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    # Get cluster layout and initial topic/partition leadership information
    await producer.start()
    try:
        # Produce message
        await producer.send_and_wait("my_topic", b"Super message")
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(consume())
    asyncio.run(send_one())
