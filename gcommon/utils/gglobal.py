# -*- coding: utf-8 -*-
# created: 2021-06-28
# creator: liguopeng@liguopeng.net

from gcommon.utils.gyaml import YamlConfigParser


class Global(object):
    # 当前进程的工作模式（如果有多种模式），空串代表不支持多模式切换，或采用缺省模式
    working_mode = ""

    # 从环境变量、命令行、配置文件加载的配置
    config = YamlConfigParser()

    @classmethod
    def set_config(cls, config: YamlConfigParser):
        cls.config = config
