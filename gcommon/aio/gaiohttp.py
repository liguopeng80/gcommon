# -*- coding: utf-8 -*-
# created: 2021-06-23
# creator: liguopeng@liguopeng.net
import logging
import traceback
from functools import wraps

from quart import Blueprint, Quart, has_request_context, json, jsonify, request
from quart.logging import default_handler
from werkzeug.exceptions import HTTPException, NotFound

from gcommon.aio import gasync
from gcommon.error import GErrors
from gcommon.error.gerror import GError, GExcept
from gcommon.utils.gglobal import Global
from gcommon.utils.gjsonobj import JsonObject
from gcommon.web.web_utils import WebConst

logger = logging.getLogger("http")


PASSTHROUGH_HTTP_ERROR = True


def web_response(result, *args, **kws):
    r = JsonObject()

    r.code = result.code
    r.message = result.desc

    paginator = kws.get("paginator", None)
    if paginator:
        r["pageSize"] = paginator.page_size
        r["current"] = paginator.current_page

        if paginator.total:
            r["total"] = paginator.total

        kws.pop("paginator")

    if args:
        assert not kws
        if len(args) > 1:
            r["data"] = args
        else:
            r["data"] = args[0]
    elif kws:
        r.data = JsonObject()
        for key, value in kws.items():
            r.data[key] = value

    return jsonify(r)


def web_response_ok(*args, **kws):
    return web_response(GErrors.ok, *args, **kws)


def web_response_paginator(paginator, *args, **kws):
    return web_response(GErrors.ok, *args, paginator=paginator, **kws)


def web_exception_response(error: GExcept, **kwargs):
    r = JsonObject()

    r.code = error.cmd_error
    r.message = error.message
    if kwargs:
        r.message = r.message % kwargs

    return jsonify(r)


def web_error_response(error: GError, desc="", **kwargs):
    r = JsonObject()

    r.code = error.code
    r.message = desc or error.desc
    if kwargs:
        r.message = r.message % kwargs

    return jsonify(r)


def web_assert(cond, error: GError, desc="", **kwargs):
    if not cond:
        raise GExcept(error, desc, **kwargs)


def web_if(cond, error: GError, desc="", **kwargs):
    if cond:
        raise GExcept(error, desc, **kwargs)


class ExceptionMiddleware(object):
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            resp = await self.app(scope, receive, send)
        except GExcept as ge:
            resp = web_exception_response(ge)
        except:
            resp = web_error_response(GErrors.gen_server_internal)
        finally:
            logger.info("---- with response: %s", request.path, resp)
            return resp


async def handle_bad_request(e):
    if PASSTHROUGH_HTTP_ERROR and isinstance(e, HTTPException):
        return e

    if isinstance(e, GExcept):
        resp = web_exception_response(e)
    else:
        resp = web_error_response(GErrors.gen_server_internal, desc=str(e) or str(type(e)))

    if type(e) == NotFound:
        pass
    else:
        logger.error(
            "request (from %s): %s %s - %s",
            request.remote_addr,
            request.method,
            request.full_path,
            traceback.format_exc(),
        )
        # logger.error("request (from %s): %s %s - %s",
        #             request.remote_addr, request.method, request.full_path, e)
    return resp


async def log_request_and_response(response):
    """web 服务器的 access log"""
    if type(request.routing_exception) == NotFound:
        logger.access(
            "404 - request (from %s): %s %s",
            request.remote_addr,
            request.method,
            request.full_path,
        )
        return response

    if request.is_json and request.content_length:
        request_body = await request.get_json()
        request_body = json.dumps(request_body, ensure_ascii=False)
    else:
        request_body = await request.get_data()

    detail_response_log = getattr(request, WebConst.GCOMMON_DETAIL_RESPONSE_LOG, True)

    if not detail_response_log:
        response_body = "..."
    elif FlaskLogManager.should_ignore_response_body(request.path):
        response_body = "..."
    elif response.is_json:
        # response_body = await response.json
        response_body = await gasync.maybe_async(response.get_json)
        response_body = json.dumps(response_body, ensure_ascii=False)
    else:
        # response_body = await response.data
        response_body = await gasync.maybe_async(response.get_data)

    request_body = request_body or None
    logger.access(
        "request (from %s): %s %s - %s, response: %s",
        request.remote_addr,
        request.method,
        request.full_path,
        request_body,
        response_body,
    )

    return response


async def read_json_request():
    data = await request.get_json()
    return JsonObject(data)


def create_quart_blueprint(name, import_name=""):
    """创建 quart blueprint"""
    blueprint = Blueprint(name, import_name or name)
    return blueprint


def create_quart_app(name, static_url_path="", static_folder=""):
    """创建 quart app，并注入 middleware"""
    global PASSTHROUGH_HTTP_ERROR
    PASSTHROUGH_HTTP_ERROR = Global.config.get("common.http.passthrough_http_error")

    app = Quart(name, static_folder=static_folder, static_url_path=static_url_path)
    app.register_error_handler(Exception, handle_bad_request)
    app.after_request(log_request_and_response)

    # app.asgi_app = ExceptionMiddleware(app.asgi_app)
    return app


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


request_formatter = RequestFormatter(
    "%(asctime)-15s %(levelname)-3s %(name)-8s %(remote_addr)s" " requested %(url)s %(message)s"
)


default_handler.setFormatter(request_formatter)
# serving_handler.setFormatter(RequestFormatter("%(t)s %(r)s %(s)s %(b)s"))
logging.getLogger("quart.serving").setLevel(logging.ERROR)


def disable_detail_response_log(f):
    """禁止详细响应日志"""

    @wraps(f)
    async def wrap(*args, **kwargs):
        setattr(request, WebConst.GCOMMON_DETAIL_RESPONSE_LOG, False)
        return await gasync.maybe_async(f, *args, **kwargs)

    return wrap


class FlaskLogManager(object):
    _path_without_detail_response_log = set()

    @classmethod
    def disable_detail_response_log_by_path(cls, path):
        """禁止详细响应日志"""
        cls._path_without_detail_response_log.add(path)

    @classmethod
    def should_ignore_response_body(cls, uri: str):
        """判断是否应该输出详细日志"""
        for path in cls._path_without_detail_response_log:
            if uri.find(path) >= 0:
                return True

        return False
