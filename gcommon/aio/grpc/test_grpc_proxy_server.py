# -*- coding: utf-8 -*-
# created: 2021-07-31
# creator: liguopeng@liguopeng.net

import asyncio
import logging

import grpc

from gcommon.aio.grpc.grpc_proxy import GrpcProxyHelper
from gcommon.aio.grpc.proto import helloworld_pb2_grpc


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def __init__(self):
        self._proxy = GrpcProxyHelper(helloworld_pb2_grpc.GreeterStub, server="localhost:50051")
        self._proxy.set_proxy(self)


async def serve() -> None:
    server = grpc.aio.server()
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    listen_addr = "[::]:12580"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
