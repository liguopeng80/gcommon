#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: 2022-01-13
# creator: liguopeng@liguopeng.net

import abc


class DatabaseManager(object):
    @abc.abstractmethod
    def async_session(self):
        pass

    @abc.abstractmethod
    def create_session(self):
        pass
