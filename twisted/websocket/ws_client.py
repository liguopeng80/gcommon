#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-02-09
import traceback

from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint

from gcommon.utils.gcounter import Sequence, Counter
from gcommon.utils.gjsonobj import JsonObject

import logging

logger = logging.getLogger('client')


class WsJsonClientProtocol(WebSocketClientProtocol):
    authenticated = False
    _sequence = Sequence()
    _active_clients = Counter()

    def __init__(self):
        WebSocketClientProtocol.__init__(self)
        self.client_id = self._sequence.next_value()

    def onOpen(self):
        logger.info('[%06x], connected to server (WS). total clients: %s.', self.client_id, self._active_clients)
        self._on_transport_connected()

    def onConnect(self, response):
        logger.info('[%06x], connecting to server (WS). total clients: %s.', self.client_id, self._active_clients)

    def onMessage(self, payload, isBinary):
        message = JsonObject.loads(payload)
        logger.debug('[%06x], message received: %s', self.client_id, message.dumps(indent=4))

        try:
            self._on_message_received(message)
        except:
            stack = traceback.format_stack()
            logger.error('[%06x] - error in onMessage: %s.', self.client_id, stack)

    def onClose(self, was_clean, code, reason):
        self._active_clients.dec()
        logger.info('[%06x], connection lost (WS). total clients: %s.', self.client_id, self._active_clients)
        print("connection closed: ", was_clean, code, reason)
        self._on_transport_closed()

    def connectionMade(self):
        WsJsonClientProtocol._active_clients.inc()
        logger.info('[%06x], connected to server (TCP). total clients: %s.', self.client_id, self._active_clients)
        WebSocketClientProtocol.connectionMade(self)

    def send_message(self, message: JsonObject):
        data = message.dumps()
        self.sendMessage(data.encode('utf8'))

    def _on_transport_connected(self):
        raise NotImplemented('for sub-class')

    def _on_transport_closed(self):
        raise NotImplemented('for sub-class')

    def _on_message_received(self, message: JsonObject):
        raise NotImplemented('sub-class')

    def _close_transport(self):
        logger.info('[%06x], client closes the connection.', self.client_id)
        self.sendClose()

    def _send_text_message(self, payload):
        logger.debug('[%06x] - message sent, content: %s.', self.client_id, payload)
        self.sendMessage(payload, False)


def create_ws_client(server, port, client_class):
    factory = WebSocketClientFactory()
    factory.setProtocolOptions(openHandshakeTimeout=600, closeHandshakeTimeout=10)
    factory.protocol = client_class

    point = TCP4ClientEndpoint(reactor, server, port)
    d = point.connect(factory)

    # reactor.connectTCP(server, port, factory)
    return d
