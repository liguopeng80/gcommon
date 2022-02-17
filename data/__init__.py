# -*- coding: utf-8 -*-
# created: 2021-04-19
# creator: liguopeng@liguopeng.net

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


class BaseManager(object):
    @property
    def _url(self):
        raise NotImplementedError("sync url")

    @property
    def _async_url(self):
        raise NotImplementedError("async url")

    @property
    def engine(self):
        return create_engine(self._url, echo=False, pool_pre_ping=True, pool_recycle=10 * 60)

    @property
    def async_engine(self):
        return create_async_engine(self._async_url, echo=False, pool_pre_ping=True, pool_recycle=10 * 60)

    def session(self):
        return sessionmaker(self.engine, expire_on_commit=False)()

    def async_session(self):
        return sessionmaker(self.async_engine, expire_on_commit=False, class_=AsyncSession)()
