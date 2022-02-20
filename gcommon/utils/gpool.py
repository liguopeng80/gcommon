# -*- coding: utf-8 -*-
# created: 2021-12-09
# creator: liguopeng@liguopeng.net

from collections import deque


class Resource(object):
    def __init__(self, pool, item=None):
        self._pool = pool
        self._item = item

    def __enter__(self):
        assert self._item
        return self._item

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._pool.append(self._item)

    async def __aenter__(self):
        if self._item:
            return self._item

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._pool.append(self._item)


class ResourcePool(object):
    def __init__(self):
        self._pool = deque()

    def append(self, item):
        self._pool.append(item)

    def get_resource(self):
        if self._pool:
            item = self._pool.popleft()
        else:
            item = None

        return Resource(self, item)
