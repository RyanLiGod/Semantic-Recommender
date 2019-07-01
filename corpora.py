#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Wu Yuanchao <151050012@hdu.edu.cn>

import logConfig
import logging
import os
import codecs

logger = logging.getLogger()


class CorporaWithTitle():
    def __init__(self, cutedfile):
        self.f = cutedfile

    def __iter__(self):
        with codecs.open(self.f, 'r', 'utf-8') as f:
            for line in f:
                cols = line.strip().lower().split(' ')
                yield cols[0], cols[1:]


class CorporaWithoutTitle():
    def __init__(self, cuted_file):
        self.f = cuted_file

    def __iter__(self):
        with codecs.open(self.f, 'r', 'utf-8') as f:
            for line in f:
                cols = line.strip().lower().split(' ')
                yield cols[1:]


class CorporaCut():
    def __init__(self, rawfile, cuttor):
        self.rawfile = rawfile
        self.cuttor = cuttor

    def __iter__(self):
        with codecs.open(self.rawfile, 'r', 'utf-8') as f:
            for i, line in enumerate(f):
                cols = line.strip().split(',')
                title, content = cols[0].strip().lower(), u' '.join(cols[1:]).lower()
                tokens = self.cuttor.fltcut(content)
                if len(tokens) > 0:
                    yield title.encode('utf8'), tokens
                else:
                    logger.warn('line %d skiped' % i)


def process_rawcorpora(rawfile, target, cuttor):
    cuted_corpora = CorporaCut(rawfile, cuttor)
    with codecs.open(target, 'w', 'utf-8') as f:
        for title, tokens in cuted_corpora:
            try:
                f.write(title + ' ' + u' '.join(tokens) + os.linesep)
            except Exception, e:
                logger.error((title, tokens, e))


def load_words(dirname):
    words = set()
    for fname in os.listdir(dirname):
        print('load from ' + fname)
        for line in codecs.open(os.path.join(dirname, fname), 'r', 'utf-8'):
            for w in set(line.strip().split()):
                words.add(w)
    return words


if __name__ == '__main__':
    from mycut import FilterCut

    cuttor = FilterCut()
    r = './test/raw/paper_error.txt'
    t = './test/cut/test.txt'
    process_rawcorpora(r, t, cuttor)
