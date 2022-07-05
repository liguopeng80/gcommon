#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-05-04

import logging
import optparse
import os
import sys

from gcommon.logger import glogger
from gcommon.utils import genv, gmain
from gcommon.utils.gconfig import DefaultConfigParser
from gcommon.utils.gjsonobj import JsonObject

logger = logging.getLogger("gcommon.server")

CONFIG_FILE_NAME = "default.conf"

PROJECT_LOG_DIR = "../../../log/"
PROJECT_CONFIG_DIR = "../../../etc/"

ENV_LOG_DIR = "ENV_LOG_DIR"
ENV_CONFIG_DIR = "PROJECT_CONFIG_DIR"


ALLOWED_ACTIONS = ("start", "stop", "restart")


def check_command_line(options, args, parser):
    if args:
        parser.error("No arguments needed.")

    # if not options.action and options.action not in ALLOWED_ACTIONS:
    #     parser.error('Do you want to start or stop the services?')

    # if options.config_file:
    #     if not os.path.exists(options.config_file):
    #         parser.warning('Config file not existed: %s.' % options.config_file)


def _get_config_file_name(options):
    """配置文件，优先顺序（配置参数，环境变量，工程目录）"""
    if options.config_file:
        return options.config_file

    config_dir = genv.get_env(ENV_CONFIG_DIR)
    if config_dir:
        return os.path.join(config_dir, CONFIG_FILE_NAME)

    project_cfg_dir = genv.get_relative_folder(__file__, PROJECT_CONFIG_DIR)
    return os.path.join(project_cfg_dir, CONFIG_FILE_NAME)


def _get_config_params(config_file, options):
    cfg_root = genv.get_folder(config_file)
    # service_config = _get_service_specific_confg()
    service_config = None

    params = {
        # 'SERVICE': options.service,
        # 'INSTANCE': options.instance,
        "CFGROOT": cfg_root,
    }

    if service_config:
        params.update(service_config)

    return params


def load_server_config(cfg, options):
    config_file = _get_config_file_name(options)
    params = _get_config_params(config_file, options)

    if config_file and os.path.exists(config_file):
        cfg.read(config_file, params)

    return cfg


def init_logger(options, *, thread_logger=False, formatter=None, file_handler=True, level_names=None):
    log_folder = gmain.get_log_folder(options, JsonObject())

    # TODO: stdio_handler should be False in production environment
    glogger.init_logger(
        log_folder,
        redirect_stdio=False,
        stdio_handler=True,
        file_handler=file_handler,
        detail=options.log_line_no,
        thread_logger=options.multi_thread or thread_logger,
        formatter=formatter,
        level_names=level_names,
    )


def server_init(parse_command_line, DEFAULT_CONFIG=None):
    """辅助函数，解析命令行，初始化日志目录"""
    # 1. 解析命令行
    parser = optparse.OptionParser()
    options, args = parse_command_line(parser, sys.argv)

    # 2. 检查命令行参数
    check_command_line(options, args, parser)

    # 3. 初始化 logger
    init_logger(options)

    # 4. 加载配置项
    cfg = DefaultConfigParser(DEFAULT_CONFIG)
    cfg = load_server_config(cfg, options)

    return cfg, options
