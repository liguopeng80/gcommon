# -*- coding: utf-8 -*-
# created: 2021-04-28
# creator: liguopeng@liguopeng.net
from abc import abstractmethod

from gcommon.error import GErrors
from gcommon.error.gerror import GExcept
from gcommon.utils import gstr
from gcommon.web.web_utils import WebConst


class Paginator(object):
    def __init__(self, current_page=1, page_size=10, total=0):
        self.current_page = current_page
        self.page_size = page_size
        self.total = total

    @property
    def offset(self):
        if self.current_page < 1:
            self.current_page = 1

        return self.page_size * (self.current_page - 1)


class WebParams(object):
    current_page = 1
    page_size = 10

    _enable_camel_to_snake = True

    def __init__(self, request, paging=False):
        self.request = request

        if paging:
            self.parse_paging_param()

    @property
    def paginator(self):
        return Paginator(self.current_page, self.page_size)

    def parse_params(self, *params):
        for param in params:
            if type(param) == str:
                self.parse(param)
            elif type(param) == list:
                self.parse(*param)
            else:
                self.parse(**param)

        return self

    def parse_required(self, param_name, attr_name=None, default=None, validator=None, **validator_params):
        return self.parse(
            param_name, attr_name=attr_name, required=True, default=default, validator=validator, **validator_params
        )

    def parse(self, param_name, attr_name=None, required=False, default=None, validator=None, **validator_params):
        param_value = self._get_attribute(param_name)
        if param_value:
            if validator:
                param_value = validator(param_name, param_value, **validator_params)

        elif default is not None:
            param_value = default
        elif required:
            raise GExcept(GErrors.gen_bad_request, "param %s is required" % param_name)
        else:
            param_value = ""

        if not attr_name:
            # 驼峰转换
            if self._enable_camel_to_snake:
                attr_name = gstr.camel_to_snake(param_name)
            else:
                attr_name = param_name

        setattr(self, attr_name or param_name, param_value)
        return self

    def parse_paging_param(self):
        """Get paging params from request, aka, page & size, only capable in method GET"""
        # Process param page size
        current_page = self._get_attribute(WebConst.PARAM_CURRENT_PAGE)
        if current_page:
            self.current_page = int(current_page)
        else:
            self.current_page = WebConst.DEFAULT_PAGE

        # Process param size
        page_size = self._get_attribute(WebConst.PARAM_PAGE_SIZE)
        if page_size:
            self.page_size = min(WebConst.MAX_PAGE_SIZE, int(page_size))

        if not page_size:
            self.page_size = WebConst.DEFAULT_PAGE_SIZE

        return self

    @abstractmethod
    def _get_attribute(self, name):
        pass


class UrlParams(WebParams):
    def _get_attribute(self, name):
        """Asyncio 等 web 库，request 请求的参数名和参数值都是 binary"""
        if type(name) is str:
            name = name.encode("utf-8")

        if name in self.request.args.keys():
            value = self.request.args[name][0]
            return value.decode("utf-8")

    def _get_text_attribute(self, name):
        """Flask 等 web 库，request 请求的参数名和参数值都是 str"""
        if name in self.request.args.keys():
            return self.request.args[name]

    @classmethod
    def switch_to_text_url_params(cls):
        cls._get_attribute = cls._get_text_attribute


class JsonParams(WebParams):
    def _get_attribute(self, name):
        return self.request.get(name, None)


class TextUrlParams(WebParams):
    """Flask 等 web 库，request 请求的参数名和参数值都是 str"""

    def _get_attribute(self, name):
        if name in self.request.args.keys():
            return self.request.args[name]
