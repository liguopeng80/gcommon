# -*- coding: utf-8 -*-
# created: 2021-04-27
# creator: liguopeng@liguopeng.net

import logging
import os
import threading
from contextlib import contextmanager

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

from gcommon.utils.gobject import ObjectWithLogger

from .. import BaseManager


class SqliteDbEngine(ObjectWithLogger):
    is_debug = False

    logger = logging.getLogger("db")
    logger.setLevel(logging.INFO)

    def __init__(self, db_conn_str, pool_size=15):
        if self.is_debug:
            from sqlalchemy.pool import AssertionPool

            self.db_engine = create_engine(db_conn_str, poolclass=AssertionPool, pool_recycle=3600, echo=True)
        else:
            self.db_engine = create_engine(db_conn_str)

        self.db_metadata = MetaData(self.db_engine)
        self.db_session = sessionmaker(bind=self.db_engine)

    @contextmanager
    def create_session(self, expunge=False):
        sess = self.db_session()
        self.logger.debug("[%x] - db session create - %s", threading.get_ident(), sess)
        try:
            yield sess
        except Exception as e:
            self.logger.error(
                "[%x] - db session or app error - %s - exception: %s",
                threading.get_ident(),
                sess,
                e,
            )
            sess.rollback()
            raise
        else:
            try:
                sess.commit()
                self.logger.debug("[%x] - db session commit - %s", threading.get_ident(), sess)

                if expunge:
                    sess.expunge_all()

            except Exception as e:
                self.logger.error(
                    "[%x] - db session or app error - %s - exception: %s",
                    threading.get_ident(),
                    sess,
                    e,
                )
                sess.rollback()
                raise
        finally:
            self.logger.debug("[%x] - db session close - %s", threading.get_ident(), sess)
            sess.close()

    @staticmethod
    def create_engine(db_file, metadata=None):
        db_conn_str = "sqlite:///%s" % db_file

        if not os.path.isfile(db_file):
            if metadata:
                engine = create_engine(db_conn_str)
                metadata.create_all(bind=engine)

        return SqliteDbEngine(db_conn_str)


class SqliteManager(BaseManager):
    def __init__(self, path):
        self.path = path

    @property
    def _url(self):
        return "sqlite:///%s" % self.path

    @property
    def _async_url(self):
        return "sqlite+aiosqlite:///%s" % self.path
