#!/usr/bin/python
# -*- coding: utf-8 -*-

"""WebSocket Server."""

import logging
import traceback
from abc import abstractmethod

from quart import Websocket

from gcommon.aio import gasync
from gcommon.utils import gtime
from gcommon.utils.gcounter import Sequence
from gcommon.utils.gjsonobj import JsonObject

logger = logging.getLogger("websock")


class WebSocketConnection(object):
    """派生类需要增加自己的构造参数"""

    _client_seq = Sequence()
    _message_seq = Sequence()
    _connections = {}

    def __init__(self):
        self.client_id = self._client_seq.next_value()
        self.connection: Websocket = None
        self._running = False

    async def serve(self, connection: Websocket):
        """持续监听服务，直到断开或者出现异常"""
        self.connection = connection._get_current_object()
        self._connections[self.client_id] = self.connection

        logger.info("[%06x] - client connected, %s.", self.client_id, self.connection)

        try:
            self._running = True
            gasync.async_call_soon(self._start_service)

            while True:
                data = await self.connection.receive_json()
                data = JsonObject(data)
                await self.on_message_received(data)
        finally:
            logger.info("[%06x] - client closes transport.", self.client_id)
            self._running = False
            await self.close_connection()
            await gasync.maybe_async(self._stop_service)

    @abstractmethod
    def _start_service(self):
        pass

    @abstractmethod
    def _stop_service(self):
        pass

    async def on_message_received(self, payload: JsonObject):
        """Server received a payload from client."""
        cmd_id = payload.cid
        cmd = payload.cmd

        logger.debug(
            "[%06x] - incoming msg: %s, id: %s, payload: %s.",
            self.client_id,
            cmd,
            cmd_id,
            payload.dumps(),
        )

        try:
            await gasync.maybe_async(self._handle_ws_message, cmd_id, cmd, payload)
        except:
            stack = traceback.format_exc()
            logger.error("[%06x] - error in onMessage: %s.", self.client_id, "".join(stack))
            raise

    @abstractmethod
    def _handle_ws_message(self, msg_id, msg_type, payload: JsonObject):
        """处理 ws 消息"""
        pass

    async def send_response(self, cmd_request, cmd, data: JsonObject = None):
        """响应客户端请求"""
        payload = JsonObject()

        payload.cmd = cmd
        payload.respToCmd = cmd_request.cmd

        if cmd_request.cid:
            payload.respToCid = cmd_request.cid

        if data:
            payload.data = data

        await self.send_message(payload)

    async def send_command(self, cmd, data: JsonObject = None):
        """发送命令"""
        payload = JsonObject()
        payload.cmd = cmd

        if data:
            payload.data = data

        await self.send_message(payload)

    async def send_message(self, payload: JsonObject):
        message_sequence = self._message_seq.next_value()
        logger.debug(
            "[%06x] - outgoing msg, seq: %s, size: %s.",
            self.client_id,
            message_sequence,
            payload.dumps(),
        )

        payload.cid = str(message_sequence)
        payload.timestamp = gtime.local_time_str()

        await self.connection.send_json(payload)

    async def close_connection(self, code=0, reason=""):
        try:
            await self.connection.close(code, reason)
        finally:
            self._connections.pop(self.client_id)
