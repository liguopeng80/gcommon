# -*- coding: utf-8 -*-
# created: 2021-04-14
# creator: liguopeng@liguopeng.net

import sqlalchemy


class MysqlDB(object):
    DEFAULT_ENCODING = "utf8"
    ECHO = False

    def __init__(self, username, password, server_addr="localhost", server_port=3306):
        self.username = username
        self.password = password

        self.server_addr = server_addr
        self.server_port = server_port

    def connect_to_db(self, db_name):
        # "mysql+pymysql://root:@localhost:3306/testdb"
        url = "mysql+pymysql://{}:{}@{}:{}/{}"
        url = url.format(self.username, self.password, self.server_addr, self.server_port, db_name)

        # The return value of create_engine() is our connection object
        # db_conn = sqlalchemy.create_engine(url, echo=True, client_encoding=self.DEFAULT_ENCODING)
        db_conn = sqlalchemy.create_engine(url, echo=self.ECHO)

        # return db_conn, db_meta
        return db_conn

    def get_db_meta(self, db_conn):
        # We then bind the connection to MetaData()
        db_meta = sqlalchemy.MetaData(bind=db_conn)
        db_meta.reflect()
        return db_meta


if __name__ == "__main__":
    pass
