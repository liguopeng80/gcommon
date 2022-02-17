#!/usr/bin/python
# -*- coding: utf-8 -*-

"""WebSocket Server.

autobahn version: 0.9.3-3

    A mid-2010 draft(version hixie-76) broke compatibility with
    reverse-proxies and gateways by including 8 bytes of key data after the
    headers, but not advertising that data in a Content-Length: 8 header.

    This data was not forwarded by all intermediates, which could lead to
    protocol failure. More recent drafts (e.g., hybi-09) put the key data in a
    Sec-WebSocket-Key header, solving this problem.
"""

import logging
import traceback

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.internet import reactor

from gcommon.utils.gcounter import Sequence, Counter

logger = logging.getLogger("websock")


class ServerProtocol(WebSocketServerProtocol):
    """Now the client request is process synchronisely"""

    # Web Socket doesn't use a separated connection to retrive server
    # notifications, so WS protocol handler send a "event_check" request to
    # command handler, and then send notifications to client on the same
    # request.

    _Client_Handler_Factory = None

    _client_seq = Sequence()
    _message_seq = Sequence()
    _clients_counter = Counter()

    def __init__(self):
        WebSocketServerProtocol.__init__(self)
        self.client_id = self._client_seq.next_value()
        self._client_handler = self._Client_Handler_Factory(self.client_id, self)

    def connectionMade(self):
        ServerProtocol._clients_counter.inc()
        WebSocketServerProtocol.connectionMade(self)

    def onConnect(self, request):
        """Client is connecting and server will send response to the client."""
        logger.info(
            "[%06x] - client connecting: %s. %s Clients Online",
            self.client_id,
            request.peer,
            ServerProtocol._clients_counter,
        )

    def onOpen(self):
        """Websocket handshake completed, server can now send/receive messages."""
        logger.info("[%06x] - new connection is made.", self.client_id)

        try:
            self._client_handler.on_client_connected()
        except:
            stack = traceback.format_stack()
            logger.error("[%06x] - error in onOpen: %s.", self.client_id, stack)

    def onMessage(self, payload, is_binary):
        """Server received a payload from client."""
        if is_binary:
            logger.debug("[%06x] - incoming binary msg, size: %s.", self.client_id, len(payload))
        else:
            logger.debug(
                "[%06x] - incoming text msg, size: %s, content: %s.",
                self.client_id,
                len(payload),
                payload,
            )

        try:
            self._client_handler.on_message(payload)
        except:
            stack = traceback.format_exc()
            logger.error("[%06x] - error in onMessage: %s.", self.client_id, "".join(stack))

    def send_binary_message(self, payload):
        ServerProtocol._message_seq.next_value()
        logger.debug(
            "[%06x] - outgoing msg, seq: %s, size: %s.",
            self.client_id,
            ServerProtocol._message_seq,
            len(payload),
        )
        self.sendMessage(payload, True)

    def send_text_message(self, payload):
        # logger.debug('[%06x] - outgoing msg, size: %s, content: %s.', self.client_id, len(payload), payload)
        self.sendMessage(payload, False)

    def onClose(self, was_clean, code, reason):
        """The web socket connection has been shutdown clearly."""
        ServerProtocol._clients_counter.dec()

        logger.info(
            "[%06x] - WS connection closed. clean: %s, code: %s. %s clients online",
            self.client_id,
            was_clean,
            code,
            self._clients_counter,
        )
        logger.debug("[%06x] - reason: %s.", self.client_id, reason)
        if self._client_handler:
            self._client_handler.on_client_disconnected()
            self._client_handler = None

    # def connectionLost(self, reason):
    #     """The TCP connection has been closed."""
    #     ServerProtocol.clients_counter -= 1
    #     logger.info("[%06x] - TCP connection closed. %d clients online", self.client_id, self.clients_counter)
    #     if self._client_handler:
    #         self._client_handler.on_client_disconnected()
    #         self._client_handler = None
    #
    #     WebSocketServerProtocol.connectionLost(self, reason)

    def _welcome(self):
        """TEST: send a welcome message to client"""
        message = {"msg": "welcome"}

        self.sendDict(message)
        # self.loseConnection()
        self.sendClose()

    @classmethod
    def create_server(cls, port, func_create_client_handler, debug=False):
        ServerProtocol._Client_Handler_Factory = staticmethod(func_create_client_handler)

        factory = WebSocketServerFactory()
        factory.protocol = cls
        factory.setProtocolOptions(openHandshakeTimeout=60, closeHandshakeTimeout=10)

        # listenWS(factory)
        logger.info("WebSocket SERVER STARTED on port: %s.", port)
        reactor.listenTCP(port, factory, backlog=5000)  # @UndefinedVariable


def test():
    logger = logging.getLogger("mockproto")

    class ClientHandler:
        def __init__(self, client_id, transport):
            self.client_id = client_id
            self.transport = transport

        def on_client_connected(self):
            logger.info("client connected")

        def on_message(self, data):
            logger.info("message: %s", data)
            message = {"cmd": "welcome"}

            self.transport.send_text_message(str(message).encode("utf-8"))
            self.transport.sendClose()

        def on_client_disconnected(self):
            logger.info("client disconnected")

    def create_client_handler(client_id, transport):
        ch = ClientHandler(client_id, transport)
        return ch

    ServerProtocol.create_server(10086, create_client_handler)
    reactor.run()  # @UndefinedVariable


# Test Codes
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)-15s %(name)-6s %(levelname)-5s %(message)s",
    )

    test()
    print("Done")
