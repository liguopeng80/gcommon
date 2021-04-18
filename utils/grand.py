# -*- coding: utf-8 -*-
#
# author: Guopeng Li
# created: 27 Aug 2008

"""Util to create random data (string, int, etc)."""

import random
import string


def rand_string(length, case_sensitive=False):
    if case_sensitive:
        data = string.ascii_letters + string.digits
    else:
        data = string.ascii_uppercase + string.digits

    return ''.join(random.SystemRandom().choice(data) for _ in range(length))


