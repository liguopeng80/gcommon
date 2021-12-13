# -*- coding: utf-8 -*- 
# created: 2021-07-29
# creator: liguopeng@liguopeng.net

import logging
from copy import copy
from aiokafka import AIOKafkaConsumer
from kafka.errors import KafkaError, KafkaConnectionError

from gcommon.aio import gasync
from gcommon.utils import gtime, gerrors
from gcommon.utils.gjsonobj import JsonObject
from gcommon.utils.gobject import ObjectWithLogger

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

        self.bootstrap_servers = config.get('servers')
        self.group_id = config.get('consumer_group')
        self.security_protocol = config.get('security_protocol')
        self.sasl_mechanism = config.get('sasl_mechanism')

        self.topics = config.get('topics')
        return self


class KafkaConsumer(object):
    def __init__(self, kafka_config: KafkaConfig, callback=None):
        self.config = kafka_config

        if callback:
            self._on_kafka_message = callback

    async def consume_forever(self):
        topics = self.config.topics or [self.config.topic]
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.config.bootstrap_servers,
            group_id=self.config.group_id,
            auto_offset_reset="earliest",
            security_protocol=self.config.security_protocol,
            sasl_mechanism=self.config.sasl_mechanism,
        )

        # Get cluster layout and join group
        logger.debug("start kafka consumer: %s", self.config.bootstrap_servers)
        try:
            await consumer.start()
        except KafkaError as kafka_error:
            logger.critical("cannot connect to kafka server: %s, error: %s",
                            self.config.bootstrap_servers, kafka_error)
            raise

        try:
            logger.debug("consume messages")
            async for message in consumer:
                try:
                    await self._process_kafka_message(message)
                except:
                    logger.error("failed to process message: %s", gerrors.format_exception_stack())

                await consumer.commit()
        except KafkaError as kafka_error:
            logger.critical("kafka consumer error: %s, error: %s",
                            self.config.bootstrap_servers, kafka_error)
            raise
        except:
            logger.critical("kafka server error: %s", self.config.bootstrap_servers)
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await consumer.stop()

    async def _process_kafka_message(self, message):
        logger.debug("message received, topic=%s, partition=%s, offset=%s, timestamp=%s",
                     message.topic, message.partition, message.offset, message.timestamp)

        event_id = f"{message.topic}-{message.partition}-{message.offset}"
        event_time = gtime.timestamp_to_date(int(message.timestamp / 1000))
        content = message.value.decode("utf-8")

        await gasync.maybe_async(self._on_kafka_message, message.topic,
                                 event_id, event_time, content)
