#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-05-14

"""异常和错误处理"""

import traceback


def format_exception_stack():
    stack = traceback.format_exc()
    return ''.join(stack)

