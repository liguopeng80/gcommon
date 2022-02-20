#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-08-31

"""计数器、计时器、序号发生器等。"""
import logging
import time
from functools import wraps

from gcommon.utils.gcounter import Counter, Gauge, Timer

logger = logging.getLogger("monitor")


def monitor(name=None):
    def monitor_decorator(func):
        @wraps(func)
        async def __inner(*args, **kwargs):
            if not name:
                func_name = func.__name__
            else:
                func_name = name
            counter = Counter.get(func_name)
            if not counter:
                counter = Counter(func_name)

            counter.inc()
            gauge_name = "%s_active" % func_name
            timer_name = "%s_time" % func_name
            with Gauge.create(gauge_name), Timer.create(timer_name):
                result = await func(*args, **kwargs)

            logger.debug(
                "function %s counter %s active %s",
                func_name,
                counter.value,
                Counter.get(gauge_name).value,
            )
            return result

        return __inner

    return monitor_decorator


@monitor()
def monitor_test():
    print("monitor test function begin....")
    time.sleep(1)
    print("monitor test function end....")


def demo():
    monitor_test()
    func_name = monitor_test.__name__
    # func_name="aaa"
    counter = Counter.get(func_name)
    print("func %s counter is %s" % (func_name, counter.value))
    gauge_name = func_name + "_active"
    gauge = Counter.get(gauge_name)
    print("func %s gauge is %s" % (gauge_name, gauge))
    timer_name = func_name + "_time"
    timer = Timer.get(timer_name)
    print("func %s time is %d" % (timer_name, timer.clear()))


if __name__ == "__main__":
    demo()
    print("Done")
