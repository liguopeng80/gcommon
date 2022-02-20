# -*- coding: utf-8 -*-
# created: 2021-07-29
# creator: liguopeng@liguopeng.net
import logging
from copy import copy
from datetime import datetime
from typing import Any, Callable

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from kafka.errors import KafkaError

from gcommon.aio import gasync
from gcommon.utils import gerrors, gtime
from gcommon.utils.gjsonobj import JsonObject

logger = logging.getLogger("kafka")


class KafkaConfig(object):
    API_VERSION = (0, 10)

    bootstrap_servers = ""
    group_id = __file__
    topic = ""
    topics = []

    security_protocol = "PLAINTEXT"
    sasl_mechanism = "PLAIN"
    sasl_plain_username = ""
    sasl_plain_password = ""

    # offset_reset = "earliest"
    offset_reset = "latest"
    auto_commit = False

    def clone(self):
        return copy(self)

    @staticmethod
    def create(config: JsonObject):
        self = KafkaConfig()

        self.bootstrap_servers = config.get("servers")
        self.group_id = config.get("consumer_group")
        self.security_protocol = config.get("security_protocol")
        self.sasl_mechanism = config.get("sasl_mechanism")

        if config.offset:
            self.offset_reset = config.offset

        if config.enable_dynamic_group:
            # 动态组，每次变更组名
            self.group_id = self.group_id + f"-{int(gtime.Timestamp.seconds())}"

        self.topics = config.get("topics")
        return self


KafkaConsumerCallback = Callable[[str, str, datetime, JsonObject], Any]


class KafkaConsumer(object):
    """
    callback -> KafkaConsumerCallback(topic, event_id, event_time, content)
    """

    Message_Content_Is_Json = True

    def __init__(self, kafka_config: KafkaConfig, callback: KafkaConsumerCallback = None):
        self.config = kafka_config

        if callback:
            self._on_kafka_message = callback

    async def consume_forever(self):
        """从制定 topic 中消费数据"""
        topics = self.config.topics or [self.config.topic]
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.config.bootstrap_servers,
            group_id=self.config.group_id,
            auto_offset_reset=self.config.offset_reset,
            security_protocol=self.config.security_protocol,
            sasl_mechanism=self.config.sasl_mechanism,
        )

        # Get cluster layout and join group
        logger.debug("start kafka consumer: %s", self.config.bootstrap_servers)
        try:
            await consumer.start()
        except KafkaError as kafka_error:
            logger.critical(
                "cannot connect to kafka server: %s, error: %s",
                self.config.bootstrap_servers,
                kafka_error,
            )
            raise

        try:
            logger.debug("consume messages")
            async for message in consumer:
                try:
                    await self._process_kafka_message(message)
                except:
                    logger.error(
                        "failed to process message: %s",
                        gerrors.format_exception_stack(),
                    )

                await consumer.commit()
        except KafkaError as kafka_error:
            logger.critical(
                "kafka consumer error: %s, error: %s",
                self.config.bootstrap_servers,
                kafka_error,
            )
            raise
        except:
            logger.critical("kafka server error: %s", self.config.bootstrap_servers)
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await consumer.stop()

    async def _process_kafka_message(self, message):
        logger.debug(
            "message received, topic=%s, partition=%s, offset=%s, timestamp=%s",
            message.topic,
            message.partition,
            message.offset,
            message.timestamp,
        )

        event_id = f"{message.topic}-{message.partition}-{message.offset}"
        event_time = gtime.timestamp_to_date(int(message.timestamp / 1000))
        content = message.value.decode("utf-8")
        if self.Message_Content_Is_Json:
            content = JsonObject.loads(content)

        await gasync.maybe_async(self._on_kafka_message, message.topic, event_id, event_time, content)


class KafkaProducer(object):
    def __init__(self, kafka_config: KafkaConfig):
        self.config = kafka_config
        self.started = False
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.config.bootstrap_servers,
            security_protocol=self.config.security_protocol,
            sasl_mechanism=self.config.sasl_mechanism,
        )

    async def init(self):
        # Get cluster layout and initial topic/partition leadership information
        await self.producer.start()
        self.started = True

    async def send_json(self, topic, message: JsonObject, key=None):
        # Produce message
        assert self.started
        value = message.dumps(ensure_ascii=False).encode("utf-8")
        await self.producer.send_and_wait(topic, value=value, key=key)

    async def stop(self):
        # Wait for all pending messages to be delivered or expire.
        if self.started:
            await self.producer.stop()
            self.started = False
