#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Wu Yuanchao <151050012@hdu.edu.cn>

import logConfig
import logging
import codecs
import os
import jieba

logger = logging.getLogger()


class FilterCut():

    # def __init__(self, user_dict_file='/home/tdlab/recommender/data180526/dict/userdict.txt'):
    def __init__(self, user_dict_file='/data/Recommender/data180526/dict/userdict.txt'):
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


if __name__ == '__main__':
    mycuttor = FilterCut('./test/d.txt')
    print ' '.join(jieba.cut(u'我来到北京进行大数据推荐'))
    print ' '.join(mycuttor.fltcut(u'我来到北京进行大数据推荐'))
