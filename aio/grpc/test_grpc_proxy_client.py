# -*- coding: utf-8 -*-
# created: 2021-07-31
# creator: liguopeng@liguopeng.net

import asyncio
import logging

import grpc

from gcommon.aio.grpc.proto import helloworld_pb2, helloworld_pb2_grpc


async def run() -> None:
    async with grpc.aio.insecure_channel("localhost:12580") as channel:
        stub = helloworld_pb2_grpc.GreeterStub(channel)

        for i in range(10):
            response = await stub.SayHello(helloworld_pb2.HelloRequest(name="you"))
            print("Greeter client received: " + response.message)


if __name__ == "__main__":
    logging.basicConfig()
    asyncio.run(run())
