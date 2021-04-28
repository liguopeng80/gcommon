#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-08-19

import logging
import hashlib
import binascii


from twisted.web import resource
from twisted.internet.defer import Deferred
from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor

from gcommon.utils.gjsonobj import JsonObject
from gcommon.twisted.gasync import pass_through_cb

from gcommon.error.gerror import *

from .web_router import WebNavigator
from .web_utils import WebConst
from ...error import GErrors

post_client = None

logger = logging.getLogger('webbase')


def router(url_pattern, **args):
    def __inner(func):
        setattr(func, WebConst.ROUTER_PARAM_PATH, url_pattern)
        setattr(func, WebConst.ROUTER_PARAM_OPT, args)

        # Save original param list in function for wrapping
        arg_names = func.__code__.co_varnames[1:func.__code__.co_argcount]
        setattr(func, WebConst.ROUTER_PARAM_VIEW_FUNC_PARAMS, arg_names)
        return func
    return __inner


class ApiRouter(object):
    def __init__(self, base_uri):
        self.base_uri = base_uri

    def get(self, uri, **kwargs):
        return self._wrapper(uri, WebConst.REQUEST_METHOD_GET, **kwargs)

    def post(self, uri, **kwargs):
        return self._wrapper(uri, WebConst.REQUEST_METHOD_POST, **kwargs)

    def _wrapper(self, uri, method, **kwargs):
        return router(self.base_uri + uri, method=method, **kwargs)


class HttpWebBase(resource.Resource):
    """ Base providing web service
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
        if 'x-real-ip' in request.requestHeaders._rawHeaders:
            real_ip = str(request.requestHeaders._rawHeaders['x-real-ip'][0])
        else:
            real_ip = str(request.client.host)

        logger.info('process request from %s:%s: %s', real_ip, request.client.port, path)

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

        logger.access('%s - result:%s',path, result.result)

        request.setHeader('Content-Type', 'application/json')
        return result.dumps()

    @staticmethod
    def parse_request_body(request):
        # body = request.content.read()
        req_message = JsonObject.loads(request.loaded_content)

        if isinstance(req_message, list):
            # log = (",").join([item.dumps() for item in req_message ])
            logger.debug('Request args - %s', req_message)
            
        else:
            logger.debug('Request args - %s', req_message.dumps())
            
        return req_message

    @staticmethod
    def _parse_paging_params(request):
        """ Get paging params from request, aka, page & size, only capable in method GET """
        # Process param page
        if WebConst.WEB_API_PARAM_LAST in request.args.keys():
            page = int(request.args[WebConst.WEB_API_PARAM_LAST][0])
        else:
            page = WebConst.WEB_PAGING_DEFAULT_ID

        # Process param size
        if WebConst.WEB_API_PARAM_SIZE in request.args.keys():
            size = int(request.args[WebConst.WEB_API_PARAM_SIZE][0])
        else:
            size = WebConst.WEB_PAGING_MAX_SIZE

        return page, size

    @staticmethod
    def _parse_login_params(req_message):
        email = req_message.user.email
        password = req_message.user.password

        terminal_type = req_message.terminal_type
        device = req_message.device
        return email, password, terminal_type, device

    @staticmethod
    def _verify_terminal_parameters(terminal_type, device):
        if terminal_type not in ('device', 'browser'):
            return False

        if not (device and device.device_id and device.os and device.version and device.model):
            return False

    @staticmethod
    def return_result(error, **kws):
        r = JsonObject()
        r.result = error.code
        r.result_desc = error.desc

        for key, value in kws.items():
            r[key] = value

        return r

    @staticmethod
    def _hash_strings(*args):
        content = ''.join(args)
        sha512 = hashlib.sha512(content)
        return binascii.hexlify(sha512.digest())

    @staticmethod
    def _get_token_string(token_id, token_text):
        return '%d-%s' % (token_id, token_text)


class Welcome(resource.Resource):
    isLeaf = False

    def getChild(self, name, request):
        if name == b'':
            return self
        return resource.Resource.getChild(self, name, request)

    def render_GET(self, request):
        return b"Yes, Web server is running."
