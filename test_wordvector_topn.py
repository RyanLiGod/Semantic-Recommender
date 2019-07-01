#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Copyright (C) 2017 Mu Shiqi <shiqimu@aliyun.com>


# 某个词袋中某个关键词在词向量中近邻的N个词，和对词向量建立索引该关键词计算得出的最近N个词，并比较两者

import gensim
from gensim.similarities.index import AnnoyIndexer
import codecs

topn = 20
index = 500
wordwm = '/testdata/data/wm.bin'
wordindex_path = '/testdata/data/test/wordindex%s.ind' % str(index)
print('正在加载词向量..........')
wordModel = gensim.models.Word2Vec.load_word2vec_format(wordwm, binary=True)


def compareWordVec():
    print('正在加载词向量索引.......')
    word_index = AnnoyIndexer()
    word_index.load(wordindex_path)
    # 将比较的结果写入文件中
    change_simi_output = codecs.open(r'/testdata/data/test/result/keywordIndex%sTop%s.txt' % (str(index), str(topn)),
                                     'w', 'utf-8')
    with codecs.open(r'/testdata/data/test/testKeyword.txt', 'r', 'utf-8') as text:
        sumrange = 0
        num = 0
        for each_text in text:
            each_text = each_text.strip().split(' ')[0]
            change_simi_output.write(each_text + '\n')
            change_simi_output.write('    ' + u'在词向量中近邻%d个词为:' % topn + '\n')
            wordVecSet = getWordVecTopN(change_simi_output, each_text, topn)
            change_simi_output.write('    ' + u'在词袋索引计算得出的最近%d个词为:' % topn + '\n')
            wordVecIndexSet = getWordVecIndexTopN(change_simi_output, word_index, each_text, topn)
            compare = set()
            compare = wordVecSet & wordVecIndexSet
            mingzhong = float(len(compare)) / float(len(wordVecSet))
            sumrange += mingzhong
            num += 1
            change_simi_output.write(
                u'  命中率为：' + str("%.5f%%" % (float(len(compare)) / float(len(wordVecSet)) * 100)) + '\n')
        change_simi_output.write(u'平均命中率为：' + str("%.5f%%" % (sumrange / float(num) * 100)) + '\n')


# 某个词袋中某个关键词在词向量中近邻的N个词
def getWordVecTopN(change_simi_output, keyword, n):
    wordVec = set()
    top10 = wordModel.most_similar(u'%s' % keyword, topn=n)
    for word in top10:
        wordVec.add(word[0])
        change_simi_output.write('\t' + str(word[1]) + '\t' + word[0] + '\n')
    return wordVec


# 对词袋生成索引
def createWordVecIndex(wordModel):
    print('正在生成词向量索引..........')
    word_index = AnnoyIndexer(wordModel, index)
    word_index.save(wordindex_path)


# 计算词向量建立索引该关键词计算得出的最近N个词
def getWordVecIndexTopN(change_simi_output, word_index, keyword, n):
    wordVecIndex = set()
    testword = wordModel.wv[u'%s' % keyword]
    top10wordindex = word_index.most_similar(testword, n)
    for word in top10wordindex:
        wordVecIndex.add(word[0])
        change_simi_output.write('\t' + str(word[1]) + '\t' + word[0] + '\n')
    return wordVecIndex


if __name__ == '__main__':
    # 训练词向量
    # createWordVecIndex(wordModel)
    # 计算最近邻和对比
    compareWordVec()
    # print(len(wordModel))
    print('计算完成！')
