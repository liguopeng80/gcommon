#!/usr/bin/python
# -*- coding: utf-8 -*-

"""WebSocket Server."""

import asyncio
import logging
import traceback

import websockets

from gcommon.utils.gcounter import Sequence, Gauge


logger = logging.getLogger('websock')


class WebSocketConnection(object):
    _message_seq = Sequence()

    def __init__(self, client_id, connection, path):
        self.client_id = client_id
        self.connection = connection
        self.path = path

    async def serve(self):
        """Client is connecting and server will send response to the client."""
        while True:
            payload = await self.connection.recv()
            if not payload:
                break

            self.on_message(payload, False)

    def on_message(self, payload, is_binary):
        """Server received a payload from client."""
        if is_binary:
            logger.debug('[%06x] - incoming binary msg, size: %s.', self.client_id, len(payload))
        else:
            logger.debug('[%06x] - incoming text msg, size: %s, content: %s.', self.client_id, len(payload), payload)

        try:
            self._client_handler.on_message(payload)
        except:
            stack = traceback.format_exc()
            logger.error('[%06x] - error in onMessage: %s.', self.client_id, ''.join(stack))
            raise

    async def send_binary_message(self, payload):
        logger.debug('[%06x] - outgoing msg, seq: %s, size: %s.',
                     self.client_id, self._message_seq, len(payload))
        await self.connection.send(payload, True)

    async def send_text_message(self, payload):
        # logger.debug('[%06x] - outgoing msg, size: %s, content: %s.', self.client_id, len(payload), payload)
        await self.connection.send(payload)


class WebSocketServer(object):
    """Now the client request is process synchronisely """
    _client_seq = Sequence()

    def __init__(self):
        pass

    async def on_connect(self, websocket, path):
        """Client is connecting and server will send response to the client."""
        client_id = self._client_seq.next_value()

        with Gauge.create("websocket") as counter:
            logger.info("[%06x] - client connected. %s Clients Online", client_id, counter.value)
            socket = WebSocketConnection(client_id, websocket, path)

            try:
                await socket.serve()
            except:
                logger.error("[%06x] - ws client disconnected (aborted). %s Clients Online",
                             client_id, counter.value)
            else:
                logger.info("[%06x] - ws client disconnected. %s Clients Online",
                            client_id, counter.value)

    @classmethod
    def create_server(cls, port, debug=False):
        logger.info('WebSocket SERVER STARTED on port: %s.', port)

        server = cls()
        start_server = websockets.serve(server.on_connect, "localhost", port)

        asyncio.get_event_loop().run_until_complete(start_server)
