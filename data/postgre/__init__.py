# -*- coding: utf-8 -*-
# created: 2021-04-19
# creator: liguopeng@liguopeng.net

from .. import BaseManager


class PostgreManager(BaseManager):
    def __init__(
        self,
        username: str = "",
        password: str = "",
        server_addr: str = "localhost",
        server_port: int = 5432,
        db_name: str = "",
    ):
        self.username = username
        self.password = password
        self.db_name = db_name
        self.server_addr = server_addr
        self.server_port = server_port

    @property
    def _url(self):
        return "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
            self.username,
            self.password,
            self.server_addr,
            self.server_port,
            self.db_name,
        )

    @property
    def _async_url(self):
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            self.username,
            self.password,
            self.server_addr,
            self.server_port,
            self.db_name,
        )
