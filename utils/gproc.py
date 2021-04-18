#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-02-27

"""进程辅助工具。"""

import os
import socket


def _hostname():
    return socket.gethostname().replace('-', '').lower()


def get_process_id(service_name, instance_id=0):
    """进程的标识。

    service_name: 服务名称 (gatekeeper, governor, postman, etc)
    instance_id:  服务的实例编号 (0, 1, 2, etc)
    """
    # server01.gateway.00
    if instance_id:
        proc_id = '%s.%s.%02d' % (_hostname(), service_name, instance_id)
    else:
        proc_id = '%s.%s' % (_hostname(), service_name)

    return proc_id


def get_process_unique_id(service_name, instance_id=0):
    """进程的唯一标识。

    service_name: 服务名称 (gatekeeper, governor, postman, etc)
    instance_id:  服务的实例编号 (0, 1, 2, etc)
    """
    pid = os.getpid()

    # server01.gateway.00.87312
    myid = '%s.%s.%02d.%s' % (_hostname(), service_name, instance_id, pid)

    return myid

