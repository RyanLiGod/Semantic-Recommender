#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Wu Yuanchao <151050012@hdu.edu.cn>

from mycut import FilterCut
import corpora
import similarity
from hnsw_util import HnswIndexer
import gensim
import codecs
import os


raws_2 = ['/data/Recommender/data180526/corpora/paper.txt']
cuts_2 = ['/data/Recommender/data180526/cut/paper.cut']

raws = ['/data/Recommender/data180526/corpora/paper.txt', '/data/Recommender/data180526/corpora/patent.txt',
        '/data/Recommender/data180526/corpora/project.txt']
cuts = ['/data/Recommender/data180526/cut/paper.cut', '/data/Recommender/data180526/cut/patent.cut',
        '/data/Recommender/data180526/cut/project.cut']
vecs = ['/data/Recommender/data180526/vec/paper.vec', '/data/Recommender/data180526/vec/patent.vec',
        '/data/Recommender/data180526/vec/project.vec']
indx = ['/data/Recommender/data180526/ind_hnsw/paper.ind', '/data/Recommender/data180526/ind_hnsw/patent.ind',
        '/data/Recommender/data180526/ind_hnsw/project.ind']
wm_file = '/data/Recommender/data180526/wm.bin'
basic_dir = '/data/Recommender/data180526/dict/basic'
userdict_file = '/data/Recommender/data180526/dict/userdict.txt'


def build_dictionary():
    basicset = corpora.load_words(basic_dir)
    print('basic loaded.')
    # stoplist = corpora.load_words(stop_dir)
    # print('stop list loaded.')
    # finalset = basicset - stoplist
    finalset = basicset
    with codecs.open(userdict_file, 'w', 'utf-8') as f:
        for w in finalset:
            f.write(w + os.linesep)


def cut():
    from mycut import FilterCut
    cuttor = FilterCut()
    for r, c in zip(raws, cuts):
        corpora.process_rawcorpora(r, c, cuttor)


def build_model():
    paper_cuted = cuts[0]
    sentences = corpora.CorporaWithoutTitle(paper_cuted)
    # sentences-语料库 size-维度 window-词共现窗口长度 sg-skipgram cbow二选一 min_count-最小词频 workers-线程
    model = gensim.models.word2vec.Word2Vec(sentences, size=200, window=4, sg=1, min_count=0, workers=4)
    model.save_word2vec_format(wm_file, binary=True)


def gen_vec():
    wm = gensim.models.word2vec.Word2Vec.load_word2vec_format(wm_file, binary=True)
    for c, v in zip(cuts, vecs):
        similarity.saveVecs(c, v, wm)


def build_index():
    for v, i in zip(vecs, indx):
        print 'begin' + v
        model = gensim.models.word2vec.Word2Vec.load_word2vec_format(v, binary=False)
        index = HnswIndexer(model)
        index.save(i)
        print 'finish' + v


if __name__ == '__main__':
    # 构建词袋
    # build_dictionary()
    # 分词
    # cut()
    # 训练词向量
    # build_model()
    # 文档向量化
    # gen_vec()
    # 生成索引
    build_index()
