#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-09-30
import traceback

from twisted.internet import reactor
from twisted.internet.defer import QueueUnderflow, QueueOverflow

from twisted.internet.defer import maybeDeferred, succeed, Deferred
from twisted.internet import defer
from twisted.python import failure
from gcommon.twisted.gtimer import AsyncTimer

import logging

logger = logging.getLogger('async')


def pass_through(result, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        logger.debug('pass_through, func exception: %s, \nstack: %s',
                     e,
                     ''.join(traceback.format_exc()))
        pass

    return result


def pass_through_cb(func, *args, **kwargs):
    def _pass_through(result):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.debug('pass_through, func exception: %s, \nstack: %s',
                         e,
                         ''.join(traceback.format_exc()))
            pass

        return result

    return _pass_through


def enable_timeout(d, seconds):
    """为普通 deferred 对象增加超时功能"""
    d._gcommon_delayed_call = reactor.callLater(seconds, defer.timeout, d)

    def _cancel_timer(result):
        if d._gcommon_delayed_call and d._gcommon_delayed_call.active():
            d._gcommon_delayed_call.cancel()

        d._gcommon_delayed_call = None
        return result

    d.addBoth(_cancel_timer)


class AsyncLock(object):
    """ 带超时功能的异步锁 """
    locked = False

    def __init__(self, lock_name=None):
        self.waiting_clients = []
        self.lock_name = lock_name

    def acquire(self, timeout_seconds):
        """
        尝试获取锁，如果在指定时间内拿不到锁，raise CancelledError
        :param timeout_seconds:
        :return: Deferred
        """
        if self.locked:
            d = AsyncTimer.wait(timeout_seconds)
            self.waiting_clients.append(d)
        else:
            self.locked = True
            d = Deferred()
            d.callback(self)

        logger.debug('<<< AsyncLock.acquire, self.locked:%s, self.waiting_clients:%s, timer:%s',
                     self.locked, self.waiting_clients, d)

        return d

    def release(self):
        """
        释放锁
        :return:
        """
        logger.debug('>>> AsyncLock.release, self.waiting_clients:%s', self.waiting_clients)
        assert self.locked, "Tried to release an unlocked lock"

        self.locked = False
        if self.waiting_clients:
            self.locked = True
            d = self.waiting_clients.pop(0)
            d.callback(self)

    def run(self, timeout_seconds, func, *args, **kwargs):
        """
        尝试获取锁，并运行 func，如果在指定时间内拿不到锁，raise CancelledError
        :param timeout_seconds:
        :return:
        """

        def release_callback(r):
            self.release()
            return r

        def execute(r):
            logger.debug('--- AsyncLock.run, func:%s', func.func_name)
            client_func_defer = maybeDeferred(func, *args, **kwargs)
            client_func_defer.addBoth(release_callback)
            logger.debug('--- AsyncLock.run, func:%s, client_func_defer: %s', func.func_name, client_func_defer)

            return client_func_defer

        d = self.acquire(timeout_seconds)
        d.addCallback(execute)
        return d


class AsyncEvent(object):
    """
    异步事件；在事件发生时，将事件广播给所有在等待的对象。

    事件有两种状态：激发和未激发。

    事件状态改变有两种途径：
    1. 自动重置 —— 事件发生后，将事件广播给第一个等待的接收者。
    2. 手动重置 —— 事件发生着，所有等待者都可以收到通知，直到事件状态被重置（未激发）。

    事件激发的两种模式：
    1. 普通模式 —— 激发事件，等待接收者
    2. 脉冲模式 —— 激发事件后仅通知当前存在的接收者，然后瞬间重置事件
    """

    def __init__(self, manual_reset=True, initial_state=False, initial_message=None):
        """
        manual_reset: 事件状态是否需要手动设置。
            True 表示在状态被激发后，在 reset 调用之前，事件一直处于激发状态。
        """
        self.manual_reset = manual_reset
        self.signaled = initial_state
        self.message = initial_message
        self.waiting = []

    def set(self, msg=None):
        """激发事件。"""
        self._notify(msg)

    def reset(self):
        """取消对象的激发状态"""
        self.signaled = False
        self.message = None

    def wait(self, timeout=0):
        """
        等待事件被激发。

        1. 如果事件处于激发状态，立即返回；否则加入等待队列
        2. 如果事件需要自动重置，在返回时将激发状态设置为 false
        """
        logger.debug('>>> AsyncEvent.wait, timeout:%s, signaled:%s, msg:%s, waiting:%s',
                     timeout, self.signaled, self.message, self.waiting)

        if self.signaled:
            # 已经激发，直接返回
            message = self.message
            if not self.manual_reset:
                # 自动重置事件状态
                self.reset()

            return succeed(message)
        else:
            d = AsyncTimer.wait(timeout)

            # 异步等待
            d.addErrback(pass_through, self.waiting.remove, d)
            self.waiting.append(d)
            return d

    def pulse(self, msg=None):
        """
        发送脉冲事件 —— 事件瞬间激发，然后重置。
        """
        assert not self.signaled
        assert not self.message

        logger.debug('>>> AsyncEvent.pulse, signaled:%s, msg:%s, waiting:%s', self.signaled, msg, self.waiting)

        # 发送事件
        self._notify(msg)

        # 无论有没有接收者，最后都需要重置时间状态
        self.reset()

    def _notify(self, msg):
        """自动重置：仅通知一个等待客户端；手动重置：通知所有等待者。"""
        logger.debug('>>> AsyncEvent._notify, signaled:%s, msg:%s, waiting:%s', self.signaled, msg, self.waiting)

        if isinstance(msg, Exception):
            msg = failure.Failure(exc_value=msg)

        self.message = msg
        self.signaled = True
        if not self.waiting:
            return

        if self.manual_reset:
            # 手动重置，通知所有等待者
            for d in self.waiting:
                self._notify_one_listener(d, self.message)

            self.waiting = []
        else:
            # 自动重置，仅通知一个等待者
            d = self.waiting.pop(0)
            self._notify_one_listener(d, self.message)
            self.reset()

    @staticmethod
    def _notify_one_listener(d, msg):
        """通知一个接收者"""
        logger.debug('>>> AsyncEvent._notify_one_listener, defer:%s, msg:%s', d, msg)
        AsyncTimer.cancel_timer(d)
        reactor.callLater(0, d.callback, msg)


class AsyncQueue(object):
    def __init__(self, size=None, max_count=None):
        """
        :param size: queue 最多能存放的对象数量，默认 None 表示没有限制
        :param max_count: 从 queue 中获取对象时等待的 client 的最大数量，默认 None 表示没有限制
        """
        self.queue = []
        self.waiting_clients = []
        self.size = size
        self.max_count_of_clients = max_count

    def qsize(self):
        """

        :return:
        """
        return len(self.queue)

    def empty(self):
        """

        :return: 判断 Queue 是否为空
        """
        return not self.queue

    def _cancel_get(self, d):
        logger.debug('>>> AsyncQueue._cancel_get, d: %s, queue: %s, waiting_clients: %s',
                     d, self.queue, self.waiting_clients)
        self.waiting_clients.remove(d)

    def put(self, obj):
        """

        :param obj:
        :return:
        """
        logger.debug('>>> AsyncQueue.put, queue: %s, waiting_clients: %s', self.queue, self.waiting_clients)

        if self.waiting_clients:
            logger.debug('--- AsyncQueue.put, data came: %s', obj)

            self.waiting_clients.pop(0).callback(obj)
        elif self.size is None or len(self.queue) < self.size:
            self.queue.append(obj)
        else:
            raise QueueOverflow()

    def get(self, timeout_seconds):
        """
        尝试从 queue 中获取对象，如果 queue 为空，等待。等待超时仍获取不到，raise CancelledError
        :return: 如果 queue 不为空，返回 queue 中第一个对象；
                 如果 queue 为空，返回 Deferred 对象
        """
        logger.debug('>>> AsyncQueue.get, queue: %s, waiting_clients: %s', self.queue, self.waiting_clients)

        if self.queue:
            return succeed(self.queue.pop(0))
        else:

            if self.max_count_of_clients is None or len(self.waiting_clients) < self.max_count_of_clients:
                d = AsyncTimer.wait(timeout_seconds)
                logger.debug('--- AsyncQueue.get, wait d: %s', d)

                d.addErrback(pass_through, self._cancel_get, d)
                self.waiting_clients.append(d)
            else:
                raise QueueUnderflow()

            return d


if __name__ == '__main__':
    from twisted.internet.defer import inlineCallbacks
    from gcommon.logger import glogger

    glogger.init_logger(stdio_handler=True)

    lock = AsyncLock('test_lock')

    def print_acquire_result(r):
        logger.debug('-- acquire_result:  %s', r)
        # raise Exception('haha')

    def test_lock_acquire(timeout_seconds):
        logger.debug('-- test_lock_acquire')
        d = lock.acquire(timeout_seconds)
        d.addCallback(print_acquire_result)

    # @inlineCallbacks
    def run(seconds):
        logger.debug("-- testRun")
        d = AsyncTimer.start(seconds)
        logger.debug("<<< testRun, d: %s", d)
        return d

    @inlineCallbacks
    def test_lock_run(timeout_seconds):
        d = lock.run(timeout_seconds, run, 20)
        yield d

    queue = AsyncQueue()
    reactor.callLater(0, queue.put, 'hah')
    # reactor.callLater(1, queue.get, 1)
    # reactor.callLater(1, queue.put, 'weeh')
    # reactor.callLater(2, queue.get, 2)

    def test_qsize():
        logger.debug('qsize: %s', queue.qsize())

    def test_empty():
        logger.debug('empty: %s, queue: %s', queue.empty(), queue.queue)

    # reactor.callLater(2, test_qsize)
    reactor.callLater(1, queue.get, 2)
    reactor.callLater(2, queue.put, failure.Failure(Exception('Test wahaha')))
    reactor.callLater(2, queue.get, 2)
    # reactor.callLater(2, queue.get, 2)
    # reactor.callLater(0, test_empty)

    # reactor.callLater(0, test_lock_acquire, 1)
    # reactor.callLater(0, test_lock_acquire, 2)
    # reactor.callLater(0, lock.release)
    # reactor.callLater(0, test_lock_run, 1)
    reactor.run()
