#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Wu Yuanchao <151050012@hdu.edu.cn>

import datetime
import logging
import logging.config

logging.config.fileConfig('logger.conf')
logger = logging.getLogger('recommServerLog')
logger.info('系统启动...')


def log_time(func):
    def wrap(*args, **kwargs):
        start = datetime.datetime.now()
        res = func(*args, **kwargs)
        end = datetime.datetime.now()
        delta = end - start
        logger.info('%s,%s' % (func.__name__, delta))
        return res

    return wrap


@log_time
def test(args):
    for arg in args:
        print arg
