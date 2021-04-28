#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-04-15


class WebConst(object):
    ROUTER_PARAM_PATH = '_http_router_url'
    ROUTER_PARAM_OPT = '_http_router_opt'
    ROUTER_PARAM_VIEW_FUNC_PARAMS = '_http_router_view_params'

    ROUTER_VIEW_FUNC_KWS_REQUEST = 'request'
    ROUTER_VIEW_FUNC_KWS_METHOD = 'method'

    REQUEST_METHOD_GET = 'GET'
    REQUEST_METHOD_POST = 'POST'
    REQUEST_METHOD_PUT = 'PUT'
    REQUEST_METHOD_DELETE = 'DELETE'

    REQUEST_HEADER_CONTENT_TYPE = 'Content-Type'

    WEB_API_PARAM_QUERY = 'query'
    WEB_API_PARAM_STATUS = 'status'
    WEB_API_PARAM_ORDER = 'order'
    WEB_API_PARAM_LAST = 'page'
    WEB_API_PARAM_SIZE = 'size'

    WEB_PAGING_DEFAULT_ID = 1
    WEB_PAGING_MAX_SIZE = 50

    MIME_TYPE_JSON = 'application/json'


def set_options_methods(request, post=False, get=False, put=False, delete=False, allowed_methods=None):
    methods = ['OPTIONS']
    if post:
        methods.append('POST')
    if get:
        methods.append('GET')
    if put:
        methods.append('PUT')
    if delete:
        methods.append('DEL')
    if allowed_methods:
        methods = list(set(methods).union(set(allowed_methods)))

    request.setHeader('Access-Control-Allow-Origin', '*')
    request.setHeader('Access-Control-Allow-Methods', ', '.join(methods))
    request.setHeader("Access-Control-Allow-Headers", "X-Requested-With, Content-Type, Authorization, Content-Length")
