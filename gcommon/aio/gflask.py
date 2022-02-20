# -*- coding: utf-8 -*-
# created: 2021-07-04
# creator: liguopeng@liguopeng.net

from gcommon.utils.gglobal import Global


def register_blueprint(app, module):
    server_base = Global.config.get("service.web.base_url") or ""
    module_base = server_base + module.base_url

    app.register_blueprint(module.app, url_prefix=module_base)
