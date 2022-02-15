# -*- coding: utf-8 -*-
# created: 2021-04-22
# creator: liguopeng@liguopeng.net

from .. import BaseManager


class MysqlManager(BaseManager):
    def __init__(
        self,
        username: str = "",
        password: str = "",
        server_addr: str = "localhost",
        server_port: int = 3306,
        db_name: str = "",
    ):
        self.username = username
        self.password = password
        self.db_name = db_name
        self.server_addr = server_addr
        self.server_port = server_port

    @property
    def _url(self):
        return "mysql+pymysql://{}:{}@{}:{}/{}".format(
            self.username,
            self.password,
            self.server_addr,
            self.server_port,
            self.db_name,
        )

    @property
    def _async_url(self):
        return "mysql+aiomysql://{}:{}@{}:{}/{}".format(
            self.username,
            self.password,
            self.server_addr,
            self.server_port,
            self.db_name,
        )
