#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Wu Yuanchao <151050012@hdu.edu.cn>

from mycut import FilterCut
import corpora
import similarity
from gensim.similarities.index import AnnoyIndexer
import gensim
import codecs
import os

raws = ['/testdata400/data/recommender/data0828/corpus/paper_corpus.txt','/testdata400/data/recommender/data0828/corpus/patent_corpus.txt','/data/word2vec/data/raw/project.txt']
cuts = ['/testdata400/data/recommender/data0828/cut/paper.cut','/testdata400/data/recommender/data0828/cut/patent.cut','/testdata400/data/recommender/data0828/cut/project.cut']
vecs = ['/testdata400/data/recommender/data0828/vec/paper.vec','/testdata400/data/recommender/data0828/vec/patent.vec','/testdata400/data/recommender/data0828/vec/project.vec']
indx = ['/testdata400/data/recommender/data0828/ind/paper.ind','/testdata400/data/recommender/data0828/ind/patent.ind','/testdata400/data/recommender/data0828/ind/project.ind']
wm_file = '/testdata400/data/recommender/data0828/wm.bin'
basic_dir = '/testdata400/data/recommender/data0828/dict/basic/'
stop_dir = '/testdata400/data/recommender/data0828/dict/stop'
userdict_file = '/testdata400/data/recommender/data0828/dict/userdict.txt'


def build_dictionary():
    basicset = corpora.load_words(basic_dir)
    print('basic loaded.')
    stoplist = corpora.load_words(stop_dir)
    print('stop list loaded.')
    finalset = basicset - stoplist
    with codecs.open(userdict_file,'w','utf-8') as f:
        for w in finalset:
            f.write(w + os.linesep)

def cut():
    from mycut import FilterCut
    cuttor = FilterCut()
    for r,c in zip(raws,cuts):
        corpora.process_rawcorpora(r,c,cuttor)

def build_model():
    paper_cuted = cuts[0]
    sentences = corpora.CorporaWithoutTitle(paper_cuted)
    #sentences-语料库 size-维度 window-词共现窗口长度 sg-skipgram cbow二选一 min_count-最小词频 workers-线程
    model = gensim.models.word2vec.Word2Vec(sentences,size=200,window=4,sg=1,min_count=0,workers=4)
    model.save_word2vec_format(wm_file,binary=True)

def gen_vec():
    wm = gensim.models.word2vec.Word2Vec.load_word2vec_format(wm_file,binary=True)
    for c,v in zip(cuts[:3],vecs[:3]):
        similarity.saveVecs(c,v,wm)

def build_index():
    for v,i in zip(vecs[0:3],indx[0:3]):
        model = gensim.models.word2vec.Word2Vec.load_word2vec_format(v,binary=False)
        index = AnnoyIndexer(model,100)
        index.save(i)

if __name__ == '__main__':
    #构建词袋
    build_dictionary()
    #分词
    cut()
    #训练词向量
    build_model()
    #文档向量化
    gen_vec()
    #生成索引
    build_index()


