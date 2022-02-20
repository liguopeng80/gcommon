# -*- coding: utf-8 -*-
# created: 2021-01-7
# creator: liguopeng@liguopeng.net


from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String, Text, func


class TimeStamp(sa.types.TypeDecorator):
    impl = sa.types.DateTime
    LOCAL_TIMEZONE = datetime.utcnow().astimezone().tzinfo

    def process_bind_param(self, value: datetime, dialect):
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)
            # value = value.astimezone(self.LOCAL_TIMEZONE)
        return value

    def process_result_value(self, value, dialect):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
            # value = value.astimezone(timezone.utc)
            value = value.astimezone(self.LOCAL_TIMEZONE)

        # return value.astimezone(timezone.utc)
        return value


def column_foreign_key(field, nullable=False, doc=""):
    filed_name = field.key
    table_name = field.parent.tables[0].name
    full_name = f"{table_name}.{filed_name}"

    for column in field.parent.columns.values():
        if column.name == filed_name:
            if type(column.type) == Integer:
                return Column(Integer, ForeignKey(full_name), nullable=nullable, doc=doc)
            else:
                return Column(String(32), ForeignKey(full_name), nullable=nullable, doc=doc)

    raise RuntimeError("invalid field")


def column_primary_key(doc=""):
    return Column(Integer, primary_key=True, doc=doc)


def column_string_primary_key(length=255, doc=""):
    return Column(
        String(length),
        primary_key=True,
        nullable=False,
        index=True,
        unique=True,
        doc=doc,
    )


def column_unique_string(length=255, doc=""):
    return Column(String(length), nullable=False, index=True, unique=True, doc=doc)


def column_required_string(length=255, doc=""):
    return Column(String(length), nullable=False, index=True, doc=doc)


def column_boolean(default=False, doc=""):
    return Column(Boolean, nullable=False, default=default, doc=doc)


def column_string_enum(length=32, default="", doc=""):
    return Column(String(length), nullable=False, index=True, default=default, doc=doc)


def column_integer_enum(default=0, doc=""):
    return Column(Integer, nullable=False, index=True, default=default, doc=doc)


def column_string(length=255, index=True, default="", doc=""):
    return Column(String(length), nullable=True, default=default, index=index, doc=doc)


def column_short_string(length=32, index=True, default="", doc=""):
    return Column(String(length), nullable=True, default=default, index=index, doc=doc)


def column_required_short_string(length=32, index=True, default="", doc=""):
    if default:
        return Column(String(length), nullable=False, index=index, default=default, doc=doc)
    else:
        return Column(String(length), nullable=False, index=index, doc=doc)


def column_text(doc=""):
    return Column(Text, doc=doc)


def column_integer(default=0, index=False, doc=""):
    return Column(Integer, index=index, nullable=True, default=default, doc=doc)


def column_big_integer(default=0, doc=""):
    return Column(BigInteger, nullable=False, index=True, default=default, doc=doc)


def column_integer_required(doc=""):
    return Column(Integer, nullable=False, index=True, doc=doc)


def column_datetime(doc=""):
    return Column(TimeStamp(), default=func.now(), nullable=False, doc=doc)


def column_created_date(doc=""):
    return Column(TimeStamp(), default=func.now(), nullable=False, doc=doc)


def column_updated_date(doc=""):
    # return Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, doc=doc)
    return Column(TimeStamp(), default=func.now(), onupdate=func.now(), nullable=False, doc=doc)


def first_row(result_set):
    """返回结果集中的第一行数据"""
    result = result_set.first()

    if result:
        return result[0]
