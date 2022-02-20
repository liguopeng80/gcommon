# -*- coding: utf-8 -*-
# created: 2021-06-28
# creator: liguopeng@liguopeng.net

import logging
from asyncio import current_task

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, create_async_engine
from sqlalchemy.orm import sessionmaker


class DatabaseManager(object):
    DEFAULT_ENCODING = "utf8"
    ECHO = False

    logger = logging.getLogger("db")
    logger.setLevel(logging.INFO)

    def __init__(self, username, password, db_name, server_addr="localhost", server_port=5432):
        self.username = username
        self.password = password

        self.server_addr = server_addr
        self.server_port = server_port
        self.db_conn = None

        url = "postgresql+asyncpg://{}:{}@{}:{}/{}"
        url = url.format(self.username, self.password, self.server_addr, self.server_port, db_name)

        dsn_template = "postgresql://{}:{}@{}:{}/{}"
        self.dsn = dsn_template.format(self.username, self.password, self.server_addr, self.server_port, db_name)

        # The return value of create_engine() is our connection object
        db_engine = create_async_engine(url, echo=self.ECHO, pool_pre_ping=True, pool_recycle=10 * 60)

        # return db_conn
        self.db_engine = db_engine

    def get_db_meta(self):
        # We then bind the connection to MetaData()
        db_meta = sqlalchemy.MetaData(bind=self.db_engine)
        db_meta.reflect()
        return db_meta

    def async_session(self):
        async_session_factory = sessionmaker(self.db_engine, expire_on_commit=False, class_=AsyncSession)

        return async_session_factory()

    def create_session(self):
        return self.async_session()

    async def _async_session(self):
        async_session_factory = sessionmaker(self.db_engine, expire_on_commit=False, class_=AsyncSession)

        async_session_cls = async_scoped_session(async_session_factory, scopefunc=current_task)
        sess = async_session_cls()

        self.logger.debug("db session create - %s", sess)
        try:
            yield sess
        except Exception as e:
            self.logger.error("db session or app error - %s - exception: %s", sess, e)
            sess.rollback()
            raise
        else:
            try:
                self.logger.debug("db session commit - %s", sess)
                await sess.commit()
            except Exception as e:
                self.logger.error("db session or app error - %s - exception: %s", sess, e)
                await sess.rollback()
                raise
        finally:
            self.logger.debug("db session close - %s", sess)
            # await sess.close()


if __name__ == "__main__":
    pass
