# -*- coding: utf-8 -*-
# created: 2021-12-06
# creator: liguopeng@liguopeng.net

"""General RPC Exceptions"""


class GeneralRpcException(Exception):
    """RPC 异常的基类"""

    pass


class RpcBadRouteException(GeneralRpcException):
    """路由错误，客户端应该检查路由设置，重发请求到正确的服务器"""

    pass
