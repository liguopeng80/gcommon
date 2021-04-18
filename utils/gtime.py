#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-01-14

"""Utils for date and time."""

import time
import datetime
import platform


def now_timestamp(in_milliseconds=False):
    if in_milliseconds:
        return int(time.time() * 1000)
    else:
        return int(time.time())


def to_timestamp(dt):
    """Return: POSIX-timestamp. (in seconds)"""
    posix_timestamp = time.mktime(dt.timetuple())
    return int(posix_timestamp)


def from_timestamp(timestamp):
    """
    Timestamp: POSIX-timestamp.
    POSIX timestamp: seconds from 1970.01.01 in UTC. 
    """
    # datetime.datetime.utcfromtimestamp(timestamp)
    
    posix_timestamp = timestamp
    dt = datetime.datetime.fromtimestamp(posix_timestamp)

    return dt


def past_millisecond(time_started):
    """How many milliseconds has past..."""
    return int((time.time() - time_started) * 1000)


def max_timestamp():
    if '32bit' in platform.architecture():
        max_year = 2019
    else:
        max_year = 2999

    max_dt = datetime.datetime(max_year, 12, 31, 23, 59, 59, 999999)
    return to_timestamp(max_dt)


def past_seconds(time_started):
    """从参数表示的时间值开始，已经流逝的时间"""
    diff = time.time() - time_started
    if diff < 0:
        return 0

    return diff


def has_expired(expiration_time):
    return datetime.datetime.now() > expiration_time


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


# Test Codes
if __name__ == "__main__":
    max_timestamp = max_timestamp()
    print('Done: %s' % max_timestamp)
