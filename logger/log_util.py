#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-03-16


def log_server_started(logger, service_name, version):
    logger.info('-' * 72)
    logger.info('- %s STARTED, version: %s' % (service_name, version))
    logger.info('-' * 72)

