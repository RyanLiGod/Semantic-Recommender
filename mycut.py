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

    # def __init__(self, user_dict_file='/home/tdlab/recommender/data_filter/dict/userdict.txt'):
    def __init__(self, user_dict_file='/data/Recommender/data_filter/dict/userdict.txt'):
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
    mycuttor = FilterCut('/home/tdlab/recommender/data_filter/dict/userdict.txt')
    print ' '.join(jieba.cut(u'利用生物制造及生物三维技术中3D生物打印设备通常无法实现多喷头切换的问题。设备包括：喷头架和抓取等必要装置，最后通过三维打印工艺将矫形器数字三维模型打印成形。希望该3D生物打印设备能广泛应用于人体器官打印等前沿领域'))
    print ' '.join(mycuttor.fltcut(u'利用生物制造及生物三维技术中3D生物打印设备通常无法实现多喷头切换的问题。设备包括：喷头架和抓取等必要装置，最后通过三维打印工艺将矫形器数字三维模型打印成形。希望该3D生物打印设备能广泛应用于人体器官打印等前沿领域'))
