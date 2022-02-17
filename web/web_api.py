# -*- coding: utf-8 -*-
# created: 2021-08-18
# creator: liguopeng@liguopeng.net

"""用于同步、异步的 Web API 基类

API 通常需要验证签名。主流验证方法有 json 签名、URL 参数签名、body 签名等三种。

对于 json, params 等签名算法，主要区别有几点：

1. 时戳是秒还是毫秒
2. 签名字符串的连接方式（content + timestamp + app_name + secret）
3. 签名使用的哈希算法, md5, sha1, sh256, sha512 等
"""
import binascii
import hashlib
import json
from urllib.parse import urlencode

from gcommon.aio import restapi
from gcommon.utils import gtime
from gcommon.utils.gjsonobj import JsonObject


class WebApiBase(object):
    _default_url_base = ""
    _default_callback_url_base = ""

    def __init__(self, app_name="", secret="", url_base="", callback_url_base=""):
        self.app_name = app_name
        self.secret = secret

        self.url_base = url_base or self._default_url_base
        self.callback_url_base = callback_url_base or self._default_callback_url_base

    def set_secret(self, app_name, secret, url_base=""):
        self.app_name = app_name
        self.secret = secret
        self.url_base = url_base or self._default_url_base

    @classmethod
    def load(cls, config: JsonObject):
        """
        demo_app:
          app_id: "11122233"
          app_secret: "dd32716437043643780877cd"
          url_base = "https://demo.app.com/notification/123"
        """
        self = cls(
            app_name=config.app_name or config.app_id,
            secret=config.app_secret,
            url_base=config.url_base,
        )

        return self


class SimpleWebApi(WebApiBase):
    def sign_request(self, **kwargs):
        """对参数签名并发送请求"""
        request_items = sorted(kwargs.items(), key=lambda x: x[0])
        extra_params = {
            "appname": self.app_name,
            "secret": self.secret,
            "ts": gtime.local_timestamp(in_milliseconds=True),
        }

        params = request_items + list(extra_params.items())
        params = [f"{key}:{value}" for key, value in params]
        params = "|".join(params)

        signature = hashlib.md5()
        signature.update(params.encode(encoding="utf-8"))
        signature = binascii.hexlify(signature.digest()).decode("utf-8")[:32]

        del extra_params["secret"]

        result = {}
        result.update(kwargs)
        result.update(extra_params)
        result.update({"sign": signature})
        return result

    def sign_json_request(self, json_payload):
        """签名并发送请求"""
        request_items = sorted(json_payload.items(), key=lambda x: x[0])
        extra_params = {
            "appname": self.app_name,
            "secret": self.secret,
            "ts": gtime.local_timestamp(in_milliseconds=True),
        }

        params = request_items + list(extra_params.items())
        param_strings = []
        for key, value in params:
            # 处理嵌套的 json 对象
            if type(value) == list:
                value = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            param_strings.append(f"{key}:{value}")

        params = "|".join(param_strings)

        signature = hashlib.md5()
        signature.update(params.encode(encoding="utf-8"))
        signature = binascii.hexlify(signature.digest()).decode("utf-8")[:32]

        result = {}
        result.update(extra_params)
        result.update({"sign": signature})

        del result["secret"]

        return result

    async def get(self, uri, **kwargs):
        """发送请求并解析响应 (json)"""
        url = self.url_base + uri
        signed_params = self.sign_request(**kwargs)

        signed_param_str = urlencode(signed_params)
        data = await restapi.get(url + "?%s" % signed_param_str)
        return JsonObject(data)

    async def get_text(self, uri, **kwargs):
        """发送请求并解析响应 (text)"""
        url = self.url_base + uri
        signed_params = self.sign_request(**kwargs)

        signed_param_str = urlencode(signed_params)
        data = await restapi.get_text(url + "?%s" % signed_param_str)
        return data

    async def post_json(self, uri, data=None, **kwargs):
        """发送请求并解析响应 (json)"""
        url = self.url_base + uri
        if self.secret:
            signed_params = self.sign_json_request(data)
            # signed_param_str = urlencode(signed_params)
            data.update(signed_params)

        # data = await restapi.post_json(url + "?%s" % signed_param_str, data)
        data = await restapi.post_json(url, data)
        return JsonObject(data)

    async def post_url(self, uri, data=None, **kwargs):
        """通过 URL 参数发送 POST 请求"""
        url = self.url_base + uri
        signed_params = self.sign_request(**data)

        signed_param_str = urlencode(signed_params)
        data = await restapi.post_json(url + "?%s" % signed_param_str, JsonObject())
        return JsonObject(data)
