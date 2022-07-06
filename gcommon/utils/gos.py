#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-01-14

from uuid import getnode as get_mac


def get_mac_address(sep=":"):
    mac = get_mac()
    mac_str = "%x" % mac

    if sep:
        mac_bytes = [mac_str[i: i + 2] for i in range(0, int(len(mac_str)), 2)]
        return sep.join(mac_bytes)
    else:
        return mac_str
