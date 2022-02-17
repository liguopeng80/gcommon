#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-04-23

import threading
import traceback

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, DeferredList
from twisted.internet.threads import deferToThread

from gcommon.logger.glogger import init_threading_config
from gcommon.utils.gobject import ObjectWithLogger


def twisted_callback(func):
    """decorator: 将回调发送回 twisted 线程（不在当前线程执行）"""

    def __func(*args, **kwargs):
        reactor.callFromThread(func, *args, **kwargs)

    __func.__name__ = func.__name__
    return __func


def twisted_call(func, *args, **kwargs):
    """从 twisted 线程之外，调用需要在 twisted reactor 循环内执行的函数。

    优点：可以避免锁操作。否则必须对并行访问的资源加锁。

    缺点：调用请求会在 reactor 上排队，当前线程 (twisted reactor 之外) 会被阻塞，
    直到调用请求被执行完毕。
    """
    return reactor.callFromThread(func, *args, **kwargs)


class _ThreadParam(object):
    def __init__(self):
        self.cv = threading.Condition()


class ThreadWorker(_ThreadParam):
    task = None

    def __init__(self, identity):
        _ThreadParam.__init__(self)
        self.identity = identity


class TwistedTaskPool(ObjectWithLogger):
    is_running = False
    pool_size = 4

    def __init__(self, pool_size=0):
        self.failed_tasks = []
        if pool_size:
            self.pool_size = pool_size

    @inlineCallbacks
    def start(self, workers=None):
        assert not self.is_running
        self.is_running = True
        self.failed_tasks = []

        if not workers:
            workers = [ThreadWorker(i) for i in range(self.pool_size)]

        threads = []
        for i in range(self.pool_size):
            thread = deferToThread(self.__thread_worker, workers[i])
            threads.append(thread)

        result = yield DeferredList(threads)
        self._on_finished()

    def _on_finished(self):
        pass

    def _allocate_task(self, param=None):
        raise NotImplementedError("for sub-class")

    def _do_work(self, worker):
        """在线程池中执行"""
        raise NotImplementedError("for sub-class")

    def __fetch_task(self, worker: ThreadWorker):
        with worker.cv:
            worker.task = self._allocate_task(worker)
            worker.cv.notify()

    def __thread_worker(self, worker):
        """在线程池中执行"""
        while self.is_running:
            with worker.cv:
                twisted_call(self.__fetch_task, worker)
                worker.cv.wait()

            task = worker.task
            self.logger.debug("worker, task fetched: %s", task)
            if not task:
                break

            try:
                self._do_work(worker)
            except Exception as e:
                twisted_call(self.__on_task_failed, task, e)
                self.logger.error("failed on task %s with error: \n%s", task, traceback.format_exc())
            else:
                self.logger.debug("worker, task processed: %s", task)

    def __on_task_failed(self, task, exception):
        self.failed_tasks.append((task, exception))


def test():
    import time

    logger = init_threading_config()

    class TestPool(TwistedTaskPool):
        current_task = 0
        all_tasks = 100

        def _on_finished(self):
            self.logger.info("stop reactor")
            reactor.stop()

        def _allocate_task(self, worker=None):
            # logger.debug("main, allocate task: %s (%s)", self.current_task, self.all_tasks)
            self.current_task = self.current_task + 1

            if self.current_task > self.all_tasks:
                return None

            return self.current_task

        def _do_work(self, worker):
            time.sleep(0.001)
            self.logger.info("worker, process task: %s", worker.task)
            if worker.task % 10 == 0:
                raise RuntimeError("failure on task %s" % worker.task)

    pool = TestPool()
    pool.set_logger(logger)

    reactor.callWhenRunning(pool.start)
    reactor.run()

    print(pool.failed_tasks)


if __name__ == "__main__":
    test()
