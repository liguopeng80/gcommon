# -*- coding: utf-8 -*-
# created: 2021-06-28
# creator: liguopeng@liguopeng.net
"""全局变量，保存系统需要的配置信息，以及服务实例。"""
from gcommon.utils.gservice import BaseServer
from gcommon.utils.gyaml import YamlConfigParser


class SystemHealthStatus:
    """设置和检查系统的健康状态"""

    _status = {}

    def is_health(self):
        """是否健康"""
        for _name, value in self._status.items():
            if not value:
                return False

        return True

    def detail(self) -> dict:
        """获取系统的详细状态"""
        return dict(self._status)

    def on_service_failed(self, service, index=""):
        """依赖的关键服务出现故障"""
        if index:
            name = f"{service}-{index}"
        else:
            name = service

        self._status[name] = False

    def on_service_recovered(self, service, index=""):
        """依赖的关键服务恢复正常"""
        if index:
            name = f"{service}-{index}"
        else:
            name = service

        self._status[name] = True


class Global:
    """全局对象，保存系统配置信息、服务对象示例、健康状态等关键数据。"""

    # pylint: disable=too-few-public-methods

    # 当前进程的工作模式（如果有多种模式），空串代表不支持多模式切换，或采用缺省模式
    working_mode = ""

    # 从环境变量、命令行、配置文件加载的配置
    config = YamlConfigParser()
    server: BaseServer = None
    health: SystemHealthStatus = SystemHealthStatus()

    @classmethod
    def set_config(cls, config: YamlConfigParser):
        """设置配置信息（全局配置）"""
        cls.config = config

    @classmethod
    def init(cls, logger=None):
        """初始化"""
        if hasattr(cls, "initializers"):
            for name, initializer in cls.initializers.items():
                if logger:
                    logger.info("Initializing config %s...", name)

                initializer()

    @staticmethod
    def register_initializer(func, name=None):
        """装饰器，用于注册初始化函数"""
        if name:
            Global._register_initializer(name, func)
        else:
            Global._register_initializer(func.__name__, func)

        return func

    @classmethod
    def _register_initializer(cls, name, initializer):
        """注册初始化函数"""
        if not hasattr(cls, "initializers"):
            cls.initializers = {}

        cls.initializers[name] = initializer
