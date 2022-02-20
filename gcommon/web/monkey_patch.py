# -*- coding: utf-8 -*-
# created: 2021-07-01
# creator: liguopeng@liguopeng.net
from gcommon.web import web_param
from gcommon.web.web_utils import WebConst


def monkey_patch_flask():
    web_param.UrlParams.switch_to_text_url_params()

    WebConst.PARAM_PAGE_SIZE = "pageSize"
    WebConst.PARAM_CURRENT_PAGE = "current"
