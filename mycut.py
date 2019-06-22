#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Wu Yuanchao <151050012@hdu.edu.cn>

import logConfig
import logging
import codecs
import utils
import jieba

logger = logging.getLogger()

if utils.get_host_ip() == '10.1.13.49':
    user_dict_file_path = '/home/tdlab/recommender/data_filter/dict/userdict.txt'
else:
    user_dict_file_path = '/data/Recommender/data_filter/dict/userdict.txt'


class FilterCut():

    def __init__(self, user_dict_file=user_dict_file_path):
        self.userdict = user_dict_file
        logger.info(u'正在加载自定义词典...')
        jieba.load_userdict(self.userdict)
        jieba.enable_parallel(8)
        logging.info(u'正在建构词袋...')
        self.load_word_bag()

    @logConfig.log_time
    def load_word_bag(self):
        ws = set()
        with codecs.open(self.userdict, 'r', 'utf-8') as df:
            for line in df:
                ws.add(line.strip().lower())
        self.wbag = frozenset(ws)

    def filter(self, tokens):
        return [t for t in tokens if t in self.wbag]

    def fltcut(self, text):
        return self.filter(jieba.cut(text))
