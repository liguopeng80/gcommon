# -*- coding: utf-8 -*- 
# created: 2021-08-02
# creator: liguopeng@liguopeng.net
"""
Usage (1):

class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def __init__(self):
        self._proxy = GrpcProxyHelper(helloworld_pb2_grpc.GreeterStub, server="localhost:50051")
        self._proxy.set_proxy(self)


Usage (2):

class Greeter(helloworld_pb2_grpc.GreeterServicer):
    pass

greeter = Greeter()

proxy = GrpcProxyHelper(helloworld_pb2_grpc.GreeterStub, server="localhost:50051")
proxy.set_proxy(greeter)
"""

import grpc


class GrpcProxyMethod(object):
    """生成 grpc 请求的代理函数"""
    def __init__(self, server_stub, server, method_name):
        self.server = server
        self.server_stub = server_stub
        self.method_name = method_name

    async def proxy_request(self, request, context):
        async with grpc.aio.insecure_channel(self.server) as channel:
            stub = self.server_stub(channel)
            stub_function = getattr(stub, self.method_name)
            response = await stub_function(request)
            return response


class GrpcProxyHelper(object):
    """为 grpc 服务增加代理"""
    Attr_Excluded_Methods = "_excluded_methods"

    def __init__(self, server_stub, server):
        self.server = server
        self.server_stub = server_stub

    def set_proxy(self, proxy_servicer):
        """为 servicer 设置代理函数，默认代理所有请求"""
        excluded = getattr(proxy_servicer, self.Attr_Excluded_Methods, [])

        for name in dir(proxy_servicer):
            if name.startswith("_"):
                continue

            if name in excluded:
                continue

            proxy_method = GrpcProxyMethod(self.server_stub, self.server, name)
            setattr(proxy_servicer, name, proxy_method.proxy_request)
