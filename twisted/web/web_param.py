# -*- coding: utf-8 -*- 
# created: 2021-04-28
# creator: liguopeng@liguopeng.net
from abc import abstractmethod

from gcommon.error import GErrors
from gcommon.error.gerror import GExcept
from gcommon.twisted.web.web_utils import WebConst


class WebParams(object):
    current_page = 1
    page_size = 10

    def __init__(self, request, paging=False):
        self.request = request
        if paging:
            self.parse_paging_param()

    def parse_params(self, *params):
        for param in params:
            if type(param) == str:
                self.parse(param)
            elif type(param) == list:
                self.parse(*param)
            else:
                self.parse(**param)

        return self

    def parse(self, param_name, attr_name=None, required=False, default=None, validator=None):
        param_value = self._get_attribute(param_name)
        if param_value:
            if validator:
                param_value = validator(param_name, param_value)

        elif default is not None:
            param_value = default
        elif required:
            raise GExcept(GErrors.gen_bad_request, "%s is required" % param_name)
        else:
            param_value = ""

        setattr(self, attr_name or param_name, param_value)
        return self

    def parse_paging_param(self):
        """ Get paging params from request, aka, page & size, only capable in method GET """
        # Process param page size
        current_page = self._get_attribute(WebConst.PARAM_CURRENT_PAGE)
        if current_page:
            self.current_page = int(current_page)
        else:
            self.current_page = WebConst.DEFAULT_PAGE

        # Process param size
        page_size = self._get_attribute(WebConst.PARAM_PAGE_SIZE)
        if page_size:
            self.page_size = int(page_size)
        else:
            self.page_size = WebConst.DEFAULT_PAGE_SIZE

        return self

    @abstractmethod
    def _get_attribute(self, name):
        pass


class UrlParams(WebParams):
    def _get_attribute(self, name):
        if type(name) is str:
            name = name.encode('utf-8')

        if name in self.request.args.keys():
            value = self.request.args[name][0]
            return value.decode("utf-8")


class JsonParams(WebParams):
    def _get_attribute(self, name):
        return self.request.get(name, None)
