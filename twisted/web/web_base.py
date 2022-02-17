#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-08-19

import binascii
import hashlib
import logging
from urllib.parse import urljoin

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.web import resource
from twisted.web.server import NOT_DONE_YET

from gcommon.twisted.gasync import pass_through_cb
from gcommon.utils.gjsonobj import JsonObject
from .web_router import WebNavigator
from .web_utils import WebConst
from ...error import GErrors
from ...error.gerror import GExcept
from ...utils.gurl import ensure_trailing_slash

post_client = None

logger = logging.getLogger("webbase")


def router(url_pattern, **args):
    def __inner(func):
        setattr(func, WebConst.ROUTER_PARAM_PATH, url_pattern)
        setattr(func, WebConst.ROUTER_PARAM_OPT, args)

        # Save original param list in function for wrapping
        arg_names = func.__code__.co_varnames[1: func.__code__.co_argcount]
        setattr(func, WebConst.ROUTER_PARAM_VIEW_FUNC_PARAMS, arg_names)
        return func

    return __inner


class ApiRouter(object):
    def __init__(self, base_url: str):
        self.base_url = ensure_trailing_slash(base_url)

    def get(self, uri, **kwargs):
        return self._wrapper(uri, WebConst.REQUEST_METHOD_GET, **kwargs)

    def post(self, uri, **kwargs):
        return self._wrapper(uri, WebConst.REQUEST_METHOD_POST, **kwargs)

    def _wrapper(self, uri, method, **kwargs):
        url = urljoin(self.base_url, uri)
        return router(url, method=method, **kwargs)


class HttpWebBase(resource.Resource):
    """Base providing web service
    Base Web Service class, All service api should be here
    Usage:
        all business handlers should be decorated with @router(uri, accepted_methods)
        accepted methods is 'GET' by default, leading handler param must be *request*

        e.g.    @router('/hello/world')
                def hello_world(self, request):
                    pass

                @router('/hello/world', methods=['GET', 'POST])
                def hello_world(self, request):
                    pass

        mutable parts in URI should be bracketed with '<' and '>', variable names with
        in the brackets is used as handler params

        e.g.    @router('/api/team/<team_id>/invitations')
                def _process_team_invitations(self, request, team_id)
                    pass

        add extra accepted methods is NOT supported by now, so handlers dealing with same
        RESTful API should check the request's method
    """

    isLeaf = False

    def __init__(self, config):
        resource.Resource.__init__(self)

        self._cfg = config
        self._app = WebNavigator(self)

    def getChild(self, path, request):
        return self

    def render(self, request):
        path = request.path.decode("utf-8")
        method = request.method.decode("utf-8")

        # Retrieve real ip address
        # TODO: X-Forwarded-For Check
        if "x-real-ip" in request.requestHeaders._rawHeaders:
            real_ip = str(request.requestHeaders._rawHeaders["x-real-ip"][0])
        else:
            real_ip = str(request.client.host)

        logger.info("process request from %s:%s: %s", real_ip, request.client.port, path)

        # Process request
        try:
            d = Deferred()
            reactor.callLater(0, d.callback, None)
            d.addCallback(pass_through_cb(self._app.serve, path, request, method))
            return NOT_DONE_YET
        except TypeError as e:
            result = HttpWebBase.return_result(GErrors.gen_bad_request, error_message=e.message)
        except NotImplementedError:
            result = HttpWebBase.return_result(GErrors.gen_bad_request)
        except GExcept as e:
            result = HttpWebBase.return_result(e.cmd_error, error_message=e.message)

        logger.access("%s - result:%s", path, result.result)

        request.setHeader("Content-Type", "application/json")
        return result.dumps()

    @staticmethod
    def parse_request_body(request):
        # body = request.content.read()
        req_message = JsonObject.loads(request.loaded_content)

        if isinstance(req_message, list):
            # log = (",").join([item.dumps() for item in req_message ])
            logger.debug("Request args - %s", req_message)

        else:
            logger.debug("Request args - %s", req_message.dumps())

        return req_message

    @staticmethod
    def return_result(result, *args, **kws):
        r = JsonObject()

        r.code = result.code
        r.message = result.desc

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

        return r

    @staticmethod
    def page_result(result, current_page, page_size, data):
        r = JsonObject()

        r.code = result.code
        r.message = result.desc

        r["data"] = data
        r["pageSize"] = page_size
        r["current"] = current_page

        return r

    @staticmethod
    def _hash_strings(*args):
        content = "".join(args)
        sha512 = hashlib.sha512(content)
        return binascii.hexlify(sha512.digest())

    @staticmethod
    def _get_token_string(token_id, token_text):
        return "%d-%s" % (token_id, token_text)


class Welcome(resource.Resource):
    isLeaf = False

    def getChild(self, name, request):
        if name == b"":
            return self
        return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
        return b"Yes, Web server is running."
