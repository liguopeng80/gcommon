# -*- coding: utf-8 -*-
# created: 2021-08-21
# creator: liguopeng@liguopeng.net
"""用于调试、监控的通用 web 工具（辅助 web 接口）。


- GET /system/info
- PUT /system/logger/<name>/levels/level
"""
import logging

from gcommon.aio.gaiohttp import create_quart_blueprint
from gcommon.aio.gaiohttp import web_error_response
from gcommon.aio.gaiohttp import web_response_ok
from gcommon.error import GErrors
from gcommon.utils.gglobal import Global
from gcommon.web.web_utils import WebConst


app = create_quart_blueprint("System Tools")
base_url = "/system"


@app.route("/health", methods=WebConst.GET)
async def get_system_health_status(name):
    """查看系统健康状态"""
    detail = Global.health.detail()

    if Global.health.is_health():
        return web_response_ok(detail)

    message = {"reason": "health_check_failed", "detail": detail}

    return web_error_response(GErrors.gen_server_internal, message)


@app.route("/loggers/level", methods=WebConst.GET)
async def get_all_log_levels(name):
    """查看系统的日志级别"""
    logger_levels = {name: logger.getEffectiveLevel() for name, logger in logging.Logger.manager.loggerDict.items()}

    return web_response_ok(logger_levels)


@app.route("/loggers/<name>/level", methods=WebConst.GET)
async def get_log_level(name):
    """查看系统的日志级别"""
    # 检查 logger 是否存在
    name = name.lower()
    if name == "root":
        logger = logging.getLogger()
    else:
        logger = logging.Logger.manager.loggerDict.get(name, None)
        GErrors.gen_target_not_found.raise_if(not logger, "指定的 logger name 不存在")

    level = logger.getEffectiveLevel()
    return web_response_ok(logger=name, level=level)


@app.route("/loggers/<name>/level/<level>", methods=WebConst.PUT)
async def update_log_level(name, level):
    """替换某个 logger 的日志级别

    在调用时不允许创建新的 logger.
    """
    # 检查 logger 是否存在
    name = name.lower()
    if name == "root":
        logger = logging.getLogger()
    else:
        logger = logging.Logger.manager.loggerDict.get(name, None)
        GErrors.gen_target_not_found.raise_if(not logger, "指定的 logger name 不存在")

    # 检查日志级别
    lever_names = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "warning": logging.WARN,
        "error": logging.error,
    }

    new_level = lever_names.get(level, None)
    GErrors.gen_bad_request.raise_if(new_level is None, "无效日志级别")

    # 更新级别
    old_level = logger.getEffectiveLevel()
    logger.setLevel(new_level)

    return web_response_ok(name=name, old_level=old_level)
