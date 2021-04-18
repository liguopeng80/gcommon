#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2015-03-16


def log_server_started(logger, service_name, version):
    logger.info('-' * 72)
    logger.info('- %s STARTED, version: %s' % (service_name, version))
    logger.info('-' * 72)


def log_function_call(logger):
    def _func_logger_decorator(func):
        def _func_logger(*args, **kws):
            logger.debug("%s called", func.__name__)
            return func(*args, **kws)
        
        return _func_logger
    
    return _func_logger_decorator


