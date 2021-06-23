# -*- coding: utf-8 -*- 
# created: 2021-06-23
# creator: liguopeng@liguopeng.net

from quart import jsonify

from gcommon.error.gerror import GExcept, GError
from gcommon.utils.gjsonobj import JsonObject


def web_response(result, *args, **kws):
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

    return jsonify(r)


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
