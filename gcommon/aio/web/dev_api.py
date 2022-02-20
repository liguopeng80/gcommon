# -*- coding: utf-8 -*-
# created: 2021-08-21
# creator: liguopeng@liguopeng.net

"""用于调试、监控的通用工具"""


import logging

from gcommon.aio.gaiohttp import create_quart_blueprint, web_response_ok
from gcommon.error import GErrors
from gcommon.web.web_utils import WebConst

app = create_quart_blueprint("Dev Tools")
base_url = "/dev"


@app.route("/loggers/<name>/levels/<level>", methods=WebConst.PUT)
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

    return web_response_ok(oldLevel=old_level)
