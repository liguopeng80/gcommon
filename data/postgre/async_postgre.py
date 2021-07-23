# -*- coding: utf-8 -*- 
# created: 2021-06-28
# creator: liguopeng@liguopeng.net

import logging
import sqlalchemy

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker


class DatabaseManager(object):
    DEFAULT_ENCODING = 'utf8'
    ECHO = False

    def __init__(self, username, password, db_name, server_addr='localhost', server_port=5432):
        self.username = username
        self.password = password

        self.server_addr = server_addr
        self.server_port = server_port
        self.db_conn = None

        url = 'postgresql+asyncpg://{}:{}@{}:{}/{}'
        url = url.format(self.username, self.password, self.server_addr, self.server_port, db_name)

        dsn_template = 'postgresql://{}:{}@{}:{}/{}'
        self.dsn = dsn_template.format(self.username, self.password,
                                       self.server_addr, self.server_port, db_name)

        # The return value of create_engine() is our connection object
        db_engine = create_async_engine(url, echo=self.ECHO)

        # return db_conn
        self.db_engine = db_engine

    def get_db_meta(self):
        # We then bind the connection to MetaData()
        db_meta = sqlalchemy.MetaData(bind=self.db_engine)
        db_meta.reflect()
        return db_meta

    def async_session(self):
        async_session_factory = sessionmaker(
            self.db_engine, expire_on_commit=False, class_=AsyncSession
        )

        return async_session_factory()

    def create_session(self):
        return self.async_session()


if __name__ == '__main__':
    pass
