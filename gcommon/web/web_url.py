# -*- coding: utf-8 -*-
# created: 2021-07-06
# creator: liguopeng@liguopeng.net
from gcommon.utils.gglobal import Global


def server_external_base():
    return Global.config.get("external_address.base_url") + Global.config.get("service.web.base_url")


def server_external_url(uri_config_name):
    return (
        Global.config.get("external_address.base_url")
        + Global.config.get("service.web.base_url")
        + Global.config.get(uri_config_name)
    )
