# -*- coding: utf-8 -*- 
# created: 2021-04-27
# creator: liguopeng@liguopeng.net
import logging
import optparse
import os
import sys
import traceback

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, maybeDeferred

from gcommon.logger import log_util
from gcommon.server import server_base
from gcommon.utils import gproc, genv, gmain
from gcommon.utils.gjsonobj import JsonObject
from gcommon.utils.gobject import ObjectWithLogger
from gcommon.utils.gyaml import YamlConfigParser


class SimpleServer(ObjectWithLogger):
    SERVICE_NAME = 'undefined'
    INSTANCE = 0
    VERSION = '0.0.0.0'

    DEFAULT_CONFIG = {}

    def init_server(self):
        """初始化服务器"""
        pass

    @inlineCallbacks
    def start_server(self):
        """启动服务器"""
        raise NotImplementedError('for sub-class')

    def _get_service_specific_confg(self):
        """服务器特定的配置参数"""
        return JsonObject()

    def __init__(self):
        self.options = None
        self.args = None

        self.config_file = ''
        self.log_dir = ''

        self.config = YamlConfigParser(self.DEFAULT_CONFIG)

        # 解析命令行
        parser = optparse.OptionParser()

        options, args = gmain.parse_command_line(
            self.SERVICE_NAME, parser, sys.argv, parse_service_options=self.parse_service_options
        )

        self.options, self.args = options, args

        self.verify_command_line(parser)

        # 初始化 logger
        self.init_logger()

        # 加载配置项
        self.load_server_config()

        self.full_server_name = gproc.get_process_id(self.SERVICE_NAME, int(self.options.instance))
        self.unique_server_name = gproc.get_process_unique_id(self.SERVICE_NAME, int(self.options.instance))

    def parse_service_options(self, parser: optparse.OptionParser):
        pass

    def verify_command_line(self, parser):
        # if self.args:
        #     parser.error('No arguments needed.')
        if self.options.service:
            if self.options.service != self.SERVICE_NAME:
                parser.error('bad service name. expected: %s, got: %s.'
                             % (self.SERVICE_NAME, self.options.service))
        else:
            self.options.service = self.SERVICE_NAME

        if not self.options.instance:
            self.options.instance = self.INSTANCE

        pass

    def load_server_config(self):
        default_config = JsonObject(self.DEFAULT_CONFIG)
        self.config_file = gmain.get_config_file(self.options, default_config)
        params = self.get_config_params()

        if self.config_file:
            self.config.read(self.config_file, params)

        secret_config_file = gmain.get_secret_config_file(self.options, default_config)
        if os.path.exists(secret_config_file):
            self.config.load_module("secret", secret_config_file)

        self.config.args = self.args
        self.config.options = self.options

        # todo: update service_root into cfg options
        self.config.service = JsonObject()
        self.config.service.service_root = params["SERVICE_ROOT"]

    def init_logger(self):
        server_base.init_logger(self.options)
        self.logger = logging.getLogger(self.SERVICE_NAME)

    def get_config_params(self):
        cfg_root = genv.get_folder(self.config_file)
        service_config = self._get_service_specific_confg()

        service_root = genv.get_env(gmain.ENV_PROJECT_ROOT)
        if not service_root:
            service_root = genv.get_relative_folder(__file__, gmain.PROJECT_ROOT)

        params = {
            'SERVICE': self.options.service,
            'INSTANCE': self.options.instance,
            'CFGROOT': cfg_root,
            'SERVICE_ROOT': service_root,
        }

        if service_config:
            params.update(service_config)

        return params

    def main(self):
        # 打印服务器启动信息
        log_util.log_server_started(self.logger, self.SERVICE_NAME, self.VERSION)

        reactor.callLater(0, self._service_main)
        reactor.run()

    @inlineCallbacks
    def _service_main(self):
        def __error_back(failure):
            stack = ''.join(traceback.format_tb(failure.getTracebackObject()))
            self.logger.error('failure: \n%s', stack)

            return failure

        try:
            d = maybeDeferred(self._service_main_with_exception)
            d.addErrback(__error_back)
            yield d
        except Exception as e:
            self.logger.error('server exception: %s', e)
            reactor.stop()

    @inlineCallbacks
    def _service_main_with_exception(self):
        yield maybeDeferred(self.init_server)
        yield maybeDeferred(self.start_server)

        self.logger.debug('--------- STARTED ---------')
