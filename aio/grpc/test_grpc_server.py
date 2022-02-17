# -*- coding: utf-8 -*-
# created: 2021-07-31
# creator: liguopeng@liguopeng.net

import asyncio
import logging
from datetime import datetime

import grpc

from gcommon.aio.grpc.proto import helloworld_pb2, helloworld_pb2_grpc

# Coroutines to be invoked when the event loop is shutting down.
_cleanup_coroutines = []


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    async def SayHello(
        self, request: helloworld_pb2.HelloRequest, context: grpc.aio.ServicerContext
    ) -> helloworld_pb2.HelloReply:

        logging.info("Received request, sleeping for 1 seconds...")
        # await asyncio.sleep(0.01)
        logging.info("Sleep completed, responding")

        return helloworld_pb2.HelloReply(message=f"Hello, {request.name} - {datetime.now()}! ")


async def serve() -> None:
    server = grpc.aio.server()
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()

    async def server_graceful_shutdown():
        """演示如何干净优雅的关闭服务"""
        logging.info("Starting graceful shutdown...")
        # Shuts down the server with 0 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
