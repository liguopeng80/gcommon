# -*- coding: utf-8 -*-
# created: 2021-06-30
# creator: liguopeng@liguopeng.net
import logging

from gcommon.data.postgre.async_postgre import DatabaseManager
from gcommon.data.sqlite import SqliteDbEngine
from gcommon.utils import gfile
from gcommon.utils.gglobal import Global
from gcommon.utils.gjsonobj import JsonObject


def create_db_engine(db_config: JsonObject, module, logger=None, **kwargs):
    """根据配置，加载各种不同的数据库引擎"""
    if db_config.engine == "sqlite":
        return create_sqlite_db_engine(db_config, logger, module)
    elif db_config.engine == "postgre-async":
        db_host = db_config.server_address
        db_port = db_config.server_port
        db_user = db_config.username
        db_pass = db_config.password

        database = kwargs["database"] or db_config.database

        db_manager = DatabaseManager(db_user, db_pass, database, db_host, db_port)
        return db_manager

    raise NotImplementedError(f"database {db_config.engine} is not supported")


def create_sqlite_db_engine(db_config, logger, module):
    db_file = gfile.join_path(Global.config.service.service_root, db_config.sqlite_dbfile)
    engine = SqliteDbEngine.create_engine(db_file, module._metadata)
    logger = logger or logging.getLogger("db")
    engine.set_logger(logger)
    return engine
