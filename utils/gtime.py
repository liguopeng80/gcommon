#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-01-14

"""Utils for date and time."""

import time
from datetime import datetime, timedelta
import platform


def local_timestamp(in_milliseconds=False):
    if in_milliseconds:
        return int(time.time() * 1000)
    else:
        return int(time.time())


def date_to_timestamp(dt):
    """Return: POSIX-timestamp. (in seconds)"""
    posix_timestamp = time.mktime(dt.timetuple())
    return int(posix_timestamp)


def timestamp_to_date(timestamp):
    """
    Timestamp: POSIX-timestamp.
    POSIX timestamp: seconds from 1970.01.01 in UTC. 
    """
    # datetime.utcfromtimestamp(timestamp)
    
    posix_timestamp = timestamp
    dt = datetime.fromtimestamp(posix_timestamp)

    return dt


def past_millisecond(time_started):
    """How many milliseconds has past..."""
    return int((time.time() - time_started) * 1000)


def max_timestamp():
    if '32bit' in platform.architecture():
        max_year = 2019
    else:
        max_year = 2999

    max_dt = datetime(max_year, 12, 31, 23, 59, 59, 999999)
    return date_to_timestamp(max_dt)


def past_seconds(time_started):
    """从参数表示的时间值开始，已经流逝的时间"""
    diff = time.time() - time_started
    if diff < 0:
        return 0

    return diff


def has_expired(expiration_time):
    return datetime.now() > expiration_time


class TimeHelper(object):
    start = 0

    def __init__(self, header=""):
        self.header = header

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_value, traceback):
        time_delta = time.time() - self.start

        if self.header:
            print(self.header, " - time used:", time_delta)
        else:
            print("time used:", time_delta)

        if not exc_type:
            return False
        else:
            return True


def utc_time_str():
    """返回 UCT 标准时间，按照 Java 的方式格式化：2011-02-18T08:30:30Z"""
    date_format = "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ"

    now = datetime.utcnow()
    millisecond = int(now.microsecond / 1000)

    date_str = date_format % (now.year, now.month, now.day, now.hour, now.minute, now.second, millisecond)

    return date_str


class DateUtil(object):
    TIME_DAY_START = " 00:00:00"
    TIME_DAY_END = " 23:59:59"

    @staticmethod
    def last_monday(dt: datetime):
        monday = DateUtil.this_monday(dt)
        last_monday = monday - timedelta(days=7)

        return last_monday

    @staticmethod
    def last_sunday(dt: datetime):
        monday = DateUtil.this_monday(dt)
        last_sunday = monday - timedelta(seconds=1)

        return last_sunday

    @staticmethod
    def this_monday(dt: datetime):
        monday = dt - timedelta(
            seconds=(((dt.weekday() * 24) + dt.hour) * 60 + dt.minute) * 60 + dt.second
        )

        return monday

    @staticmethod
    def this_sunday(dt: datetime):
        sunday = DateUtil.this_monday(dt) + timedelta(days=7)
        return sunday


# Test Codes
if __name__ == "__main__":
    max_timestamp = max_timestamp()
    print('Done: %s' % max_timestamp)

    print(utc_time_str())

