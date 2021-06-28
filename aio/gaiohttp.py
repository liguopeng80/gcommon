# -*- coding: utf-8 -*- 
# created: 2021-06-23
# creator: liguopeng@liguopeng.net
import logging

from quart import jsonify, Quart, json, Blueprint
from quart import has_request_context, request
from quart.logging import default_handler, serving_handler

from gcommon.error import GErrors
from gcommon.error.gerror import GExcept, GError
from gcommon.utils.gjsonobj import JsonObject

logger = logging.getLogger("http")


def web_response(result, *args, **kws):
    r = JsonObject()

    r.code = result.code
    r.message = result.desc

    paginator = kws.get("paginator", None)
    if paginator:
        r["pageSize"] = paginator.page_size
        r["current"] = paginator.current_page
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


def handle_bad_request(e):
    if isinstance(e, GExcept):
        resp = web_exception_response(e)
    else:
        resp = web_error_response(GErrors.gen_server_internal, desc=str(e))

    # logger.error("request: %s %s, response: %s",
    #              request.method, request.path, resp.response.data.decode('utf-8'))
    return resp


async def log_request_and_response(response):
    """web 服务器的 access log"""
    if request.is_json:
        request_body = await request.get_json()
        request_body = json.dumps(request_body, ensure_ascii=False)
    else:
        request_body = await request.get_data()

    if response.is_json:
        response_body = await response.json
        response_body = json.dumps(response_body, ensure_ascii=False)
    else:
        response_body = await response.data

    request_body = request_body or None
    logger.access("request (from %s): %s %s - %s, response: %s",
                  request.remote_addr, request.method, request.full_path,
                  request_body, response_body)

    return response


def create_quart_blueprint(name, import_name=""):
    """创建 quart blueprint"""
    blueprint = Blueprint(name, import_name or name)
    return blueprint


def create_quart_app(name):
    """创建 quart app，并注入 middleware"""
    app = Quart(name)
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
    "%(asctime)-15s %(levelname)-3s %(name)-8s %(remote_addr)s"
    " requested %(url)s %(message)s"
)


default_handler.setFormatter(request_formatter)
# serving_handler.setFormatter(RequestFormatter("%(t)s %(r)s %(s)s %(b)s"))
logging.getLogger('quart.serving').setLevel(logging.ERROR)
