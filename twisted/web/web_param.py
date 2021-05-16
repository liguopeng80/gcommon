# -*- coding: utf-8 -*- 
# created: 2021-04-28
# creator: liguopeng@liguopeng.net
from gcommon.error import GErrors
from gcommon.error.gerror import GExcept
from gcommon.twisted.web.web_utils import WebConst


class WebParams(object):
    current_page = 1
    page_size = 10

    def __init__(self, request, paging=False):
        self.request = request
        if paging:
            self.parse_paging_param(request)

    def parse_params(self, request, *params):
        for param in params:
            if type(param) == str:
                self.parse(request, param)
            else:
                self.parse(request, **param)

        return self

    def parse(self, param_name, attr_name=None, required=False, default=None, validator=None):
        # body = request.content.read()
        if type(param_name) is str:
            param_name = param_name.encode('utf-8')

        if param_name in self.request.args.keys():
            param_value = self.request.args[param_name][0]
            param_value = param_value.decode("utf-8")
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

    def parse_paging_param(self, request):
        """ Get paging params from request, aka, page & size, only capable in method GET """
        # Process param page size
        if WebConst.PARAM_CURRENT_PAGE in request.args.keys():
            self.current_page = int(request.args[WebConst.PARAM_CURRENT_PAGE][0])
        else:
            self.current_page = WebConst.DEFAULT_PAGE

        # Process param size
        if WebConst.PARAM_PAGE_SIZE in request.args.keys():
            self.page_size = int(request.args[WebConst.PARAM_PAGE_SIZE][0])
        else:
            self.page_size = WebConst.DEFAULT_PAGE_SIZE

        return self
