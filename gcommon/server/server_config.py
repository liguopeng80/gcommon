# -*- coding: utf-8 -*-
# created: 2021-06-29
# creator: liguopeng@liguopeng.net

from copy import copy

from gcommon.utils.gjsonobj import JsonObject


class ServerConfig(object):
    server_address = ""
    server_port = ""

    username = ""
    password = ""

    enable_ssl = ""

    def clone(self):
        return copy(self)

    @classmethod
    def load(cls, config: JsonObject):
        self = cls()

        self.server_address = config.server_address
        self.server_port = config.server_port

        self.username = config.username
        self.password = config.password

        self.enable_ssl = config.enable_ssl

        self._load_extra_config(config)

        return self

    def _load_extra_config(self, config: JsonObject):
        """派生类自定义的配置属性"""
        pass
