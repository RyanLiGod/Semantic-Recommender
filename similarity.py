#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import ConfigParser
import logging.config
import os
import time

import gensim
from gensim.similarities.index import AnnoyIndexer
from numpy import array

import utils
from annoy import AnnoyIndex
from corpora import CorporaWithTitle
from DBUtil import DB
from mycut import FilterCut
from hnsw_util import HnswIndexer
from redis_util import RedisUtil

logging.config.fileConfig('logger.conf')
logger = logging.getLogger('recommServerLog')


class Convert2Vec(object):
    def __init__(self, wm):
        self.wm = wm

    def text2v(self, text, cuttor):
        tokens = cuttor.fltcut(text)
        if len(tokens) == 0:
            return None
        else:
            return self.tokens2v(tokens)

    def tokens2v(self, tokens):
        assert len(tokens) > 0
        vectors = [self.wm[w] for w in tokens if w in self.wm]
        if len(vectors) == 0: return [0.0 for i in range(self.wm.vector_size)]
        return array(vectors).mean(axis=0)


class Corparo2Vec(object):
    def __init__(self, wm):
        self.wm = wm
        self.c2v = Convert2Vec(wm)

    def genvec(self, corparo_with_title):
        for title, tokens in corparo_with_title:
            v = self.c2v.tokens2v(tokens)
            yield title, v


def getRowCount(f):
    output = os.popen('wc -l ' + f)
    s = output.read()
    output.close()
    return s.split()[0]


def saveVecs(infile, target, wm):
    corp2v = Corparo2Vec(wm)
    corp_with_title = CorporaWithTitle(infile)
    rows = getRowCount(infile)
    with codecs.open(target, 'w', 'utf-8') as f:
        f.write('%s %s%s' % (rows, wm.vector_size, os.linesep))
        for title, vec in corp2v.genvec(corp_with_title):
            l = u'%s %s %s' % (title, ' '.join(['%.6f' % v for v in vec]), os.linesep)
            f.write(l)


class Recommander(object):
    def __init__(self, vec_file, pap, pat, pro):
        # self.wm = gensim.models.KeyedVectors.load_word2vec_format(vec_file,binary=True)
        self.wm = gensim.models.word2vec.Word2Vec.load_word2vec_format(vec_file, binary=True)

        logger.info(u'开始导入paper_index...')
        self.paper_index = HnswIndexer()
        self.paper_index.load(pap)
        logger.info(u'开始导入patent_index...')
        self.patent_index = HnswIndexer()
        self.patent_index.load(pat)
        logger.info(u'开始导入project_index...')
        self.project_index = HnswIndexer()
        self.project_index.load(pro)

        self.t2v = Convert2Vec(self.wm)
        self.cuttor = FilterCut()
        self.redis = RedisUtil()
        self.featureIndex = self.buildFeatureIndex()

    def buildFeatureIndex(self):
        if utils.get_host_ip() == '10.1.13.49':
            paperFeature = open("/home/tdlab/recommender/data180526/feature/paper_feature180526.txt", 'r')
            patentFeature = open("/home/tdlab/recommender/data180526/feature/patent_feature180526.txt", 'r')
            projectFeature = open("/home/tdlab/recommender/data180526/feature/project_feature180526.txt", 'r')
        else:
            paperFeature = open("/data/Recommender/data_filter/feature/paper_feature180526.txt", 'r')
            patentFeature = open("/data/Recommender/data_filter/feature/patent_feature180526.txt", 'r')
            projectFeature = open("/data/Recommender/data_filter/feature/project_feature180526.txt", 'r')
        featureIndex = {}
        logger.info(u'开始导入paper特征文件...')
        featureIndex['paper'] = self.loadFeature(paperFeature, 'paper')
        logger.info(u'开始导入patent特征文件...')
        featureIndex['patent'] = self.loadFeature(patentFeature, 'patent')
        logger.info(u'开始导入project特征文件...')
        featureIndex['project'] = self.loadFeature(projectFeature, 'project')
        logger.info(u'导入特征文件完成')
        return featureIndex

    def loadFeature(self, file, typee):
        file = file.readlines()
        index = {}
        index['field'] = {}
        index['type'] = {}
        index['province'] = {}
        index['unit'] = {}
        if typee == 'paper':
            index['journalQuality'] = {}
        if typee == 'patent':
            index['patentType'] = {}
        if typee == 'project':
            index['projectType'] = {}
        for line in file:
            feature = line.split('\t')
            index['field'][feature[1]] = index['field'].get(feature[1], [])
            index['field'][feature[1]].append(feature[0])
            index['type'][feature[2]] = index['type'].get(feature[2], [])
            index['type'][feature[2]].append(feature[0])
            index['province'][feature[3]] = index['province'].get(feature[3], [])
            index['province'][feature[3]].append(feature[0])
            index['unit'][feature[4]] = index['unit'].get(feature[4], [])
            index['unit'][feature[4]].append(feature[0])
            if typee == 'paper':
                index['journalQuality'][feature[7]] = index['journalQuality'].get(feature[7], [])
                index['journalQuality'][feature[7]].append(feature[0])
            if typee == 'patent':
                index['patentType'][feature[7]] = index['patentType'].get(feature[7], [])
                index['patentType'][feature[7]].append(feature[0])
            if typee == 'project':
                index['projectType'][feature[7]] = index['projectType'].get(feature[7], [])
                index['projectType'][feature[7]].append(feature[0])
        return index

    # 获取某专家的所有成果对于需求txt的按相似度排序，论文专利项目分别返回前topN
    def expertDocsSort(self, expertId, txt, topN):
        vec = self.t2v.text2v(txt, self.cuttor)
        annoy = AnnoyIndex(200)
        count = 0
        annoy.add_item(count, vec)
        count = count + 1
        db = DB()
        papers = db.getPapers(expertId)
        for p in papers:
            p[3] = self.t2v.text2v(p[1] + p[2], self.cuttor)
            if p[3] is not None:
                annoy.add_item(count, p[3])
                p[3] = annoy.get_distance(0, count)
                count = count + 1
        papers = sorted(papers, key=lambda p: p[3])
        papersFormated = []
        for p in papers:
            if len(papersFormated) == topN:
                break
            map = {}
            if p[0] is not None:
                map['paperId'] = p[0].encode('utf8')
            else:
                map['paperId'] = p[0]
            if p[1] is not None:
                map['name'] = p[1].encode('utf8')
            else:
                map['name'] = p[1]
            if p[4] is not None:
                map['authors'] = p[4].encode('utf8')
            else:
                map['authors'] = p[4]
            if p[5] is not None:
                map['journalName'] = p[5].encode('utf8')
            else:
                map['journalName'] = p[5]
            if p[6] is not None:
                map['year'] = p[6].encode('utf8')
            else:
                map['year'] = p[6]
            papersFormated.append(map)

        count = 0
        annoy.unload()
        annoy.add_item(count, vec)
        count = count + 1
        patents = db.getPatents(expertId)
        for p in patents:
            p[3] = self.t2v.text2v(p[1] + p[2], self.cuttor)
            if p[3] is not None:
                annoy.add_item(count, p[3])
                p[3] = annoy.get_distance(0, count)
                count = count + 1
        patents = sorted(patents, key=lambda p: p[3])
        patentsFormated = []
        for p in patents:
            if len(patentsFormated) == topN:
                break
            map = {}
            if p[0] is not None:
                map['patentId'] = p[0].encode('utf8')
            else:
                map['patentId'] = p[0]
            if p[4] is not None:
                map['publicationNo'] = p[4].encode('utf8')
            else:
                map['publicationNo'] = p[4]
            if p[1] is not None:
                map['name'] = p[1].encode('utf8')
            else:
                map['name'] = p[1]
            if p[5] is not None:
                map['inventors'] = p[5].encode('utf8')
            else:
                map['inventors'] = p[5]
            if p[6] is not None:
                map['applicant'] = p[6].encode('utf8')
            else:
                map['applicant'] = p[6]
            if p[7] is not None:
                map['year'] = p[7].encode('utf8')
            else:
                map['year'] = p[7]
            patentsFormated.append(map)

        count = 0
        annoy.unload()
        annoy.add_item(count, vec)
        count = count + 1
        projects = db.getProjects(expertId)
        for p in projects:
            p[3] = self.t2v.text2v(p[1] + p[2], self.cuttor)
            if p[3] is not None:
                annoy.add_item(count, p[3])
                p[3] = annoy.get_distance(0, count)
                count = count + 1
        projects = sorted(projects, key=lambda p: p[3])
        projectsFormated = []
        for p in projects:
            if len(projectsFormated) == topN:
                break
            map = {}
            if p[0] is not None:
                map['projectId'] = p[0].encode('utf8')
            else:
                map['projectId'] = p[0]
            if p[1] is not None:
                map['name'] = p[1].encode('utf8')
            else:
                map['name'] = p[1]
            if p[4] is not None:
                map['member'] = p[4].encode('utf8')
            else:
                map['member'] = p[4]
            if p[5] is not None:
                map['unit'] = p[5].encode('utf8')
            else:
                map['unit'] = p[5]
            if p[6] is not None:
                map['year'] = p[6].encode('utf8')
            else:
                map['year'] = p[6]
            if p[7] is not None:
                map['type'] = p[7].encode('utf8')
            else:
                map['type'] = p[7]
            projectsFormated.append(map)
        result = {}
        result['papers'] = papersFormated
        result['patents'] = patentsFormated
        result['projects'] = projectsFormated
        return result

    # 过滤论文，项目，专利
    def filter(self, typee, topDocs, filterParams, topN):
        topDocIds = [i for i, j in topDocs]
        if not (filterParams[0] == '' or filterParams[
            0] == '-1' or typee == 'project'):  # field, 项目没有type，不用过滤，参数为空字符串或者-1表示不过滤
            if filterParams[0] not in self.featureIndex[typee]['field']:
                topDocIds = []
            else:
                topDocIds = list(set(topDocIds).intersection(self.featureIndex[typee]['field'][filterParams[0]]))
        if not (filterParams[1] == '' or filterParams[1] == '-1'):  # type
            if filterParams[1] not in self.featureIndex[typee]['type']:
                topDocIds = []
            else:
                topDocIds = list(set(topDocIds).intersection(self.featureIndex[typee]['type'][filterParams[1]]))
        if not (filterParams[2] == '' or filterParams[2] == '-1'):  # province
            if filterParams[2] not in self.featureIndex[typee]['province']:
                topDocIds = []
            else:
                topDocIds = list(set(topDocIds).intersection(self.featureIndex[typee]['province'][filterParams[2]]))
        if not (filterParams[3] == '' or filterParams[3] == '-1'):  # unit
            if filterParams[3] not in self.featureIndex[typee]['unit']:
                topDocIds = []
            else:
                topDocIds = list(set(topDocIds).intersection(self.featureIndex[typee]['unit'][filterParams[3]]))
        if typee == 'paper' and not (filterParams[4] == '' or filterParams[4] == '-1'):  # journalQuality
            origin_doc = topDocIds
            topDocIds = []
            for param in filterParams[4]:
                topDocIds = topDocIds + list(
                    set(origin_doc).intersection(self.featureIndex[typee]['journalQuality'][param]))
        if typee == 'patent' and not (filterParams[4] == '' or filterParams[4] == '-1'):  # patentType
            if filterParams[4] not in self.featureIndex[typee]['patentType']:
                topDocIds = []
            else:
                topDocIds = list(set(topDocIds).intersection(self.featureIndex[typee]['patentType'][filterParams[4]]))
        if typee == 'project' and not (filterParams[4] == '' or filterParams[4] == '-1'):  # projectType
            if filterParams[4] not in self.featureIndex[typee]['projectType']:
                topDocIds = []
            else:
                topDocIds = list(set(topDocIds).intersection(self.featureIndex[typee]['projectType'][filterParams[4]]))
        result = []
        for i in topDocs:
            if i[0] in topDocIds:
                result.append(i)
            if len(result) == topN:
                break
        return result

    def set_ef(self, typee, ef):
        if typee == 'paper':
            self.paper_index.set_ef(ef)
        elif typee == 'patent':
            self.patent_index.set_ef(ef)
        elif typee == 'project':
            self.project_index.set_ef(ef)

    def most_similar_paper(self, text, topn=10):
        vec = self.t2v.text2v(text, self.cuttor)
        return self.paper_index.most_similar(vec, topn)

    def most_similar_patent(self, text, topn=10):
        vec = self.t2v.text2v(text, self.cuttor)
        return self.patent_index.most_similar(vec, topn)

    def most_similar_project(self, text, topn=10):
        vec = self.t2v.text2v(text, self.cuttor)
        return self.project_index.most_similar(vec, topn)

    def getSimExpertsIds(self, topDocs):
        expertInfoOut = {}
        expertMap = {}
        authorSeqWeiht = [1.0, 0.85, 0.7, 0.5]
        db_1 = time.time()
        for typee in topDocs:
            order = {}
            order[typee] = {}
            k = 0
            for i, j in topDocs[typee]:
                order[typee][i] = k
                k = k + 1
            ids = [i for i, j in topDocs[typee]]

            try:
                docExpertIds = self.redis.getAuthors(ids)  # 使用Redis获取信息
                # if len(docExpertIds) == 0:
                #     logger.info(u'Redis失效，使用sql查询')
                #     docExpertIds = self.get_author_by_sql(typee, ids)
            except:
                logger.info(u'连接不上Redis，使用sql查询')
                docExpertIds = self.get_author_by_sql(typee, ids)
            for id in docExpertIds:
                # if not db.idInDB(typee, id):
                #     print "docId: " + id + " is not in db"
                #     continue
                expertIds = docExpertIds[id]
                qs = 1.0
                sim = qs
                for i, j in topDocs[typee]:
                    if i == id:
                        sim = j * sim
                        break
                for i in range(len(expertIds)):
                    if i >= 4:  # 一个成果考虑4个作者
                        break
                    expertInfoOut[expertIds[i]] = expertInfoOut.get(expertIds[i], [])
                    expertInfoOut[expertIds[i]].append([typee + str(order[typee][id]), sim * authorSeqWeiht[i], i])
                    expertMap[expertIds[i]] = expertMap.get(expertIds[i], [])
                    expertMap[expertIds[i]].append(sim * authorSeqWeiht[i])
        db_2 = time.time()
        logger.info(u'time in 数据库 ' + str(db_2 - db_1))
        return expertMap, expertInfoOut

    # 从成果提取专家，有些专家在不过滤省份时排在前，但过滤省份后排在后，为避免此情况，先不过滤成果的地区，
    # 从这些不过滤地区的成果中提取专家，再按地区过滤专家，若不足topN，再在过滤地区的成果中找剩余的专家
    #
    # 这个函数需要重构，但是八成需求会改，所以先不重构了
    def most_similar_expert(self, topPapers, topPatents, topProjects, filterParams, expertTopN):
        file = open("config.ini", 'r')
        config = ConfigParser.ConfigParser()
        config.readfp(file)
        LEN = int(config.get('global', 'len'))  # 对于一个专家要计算多少他的成果
        COE = float(config.get('global', 'coe'))  # 对于一个专家，从第二个的成果相似度乘的系数
        topDocs = {}

        topDocs['paper'] = self.filter('paper', topPapers, filterParams, 50)
        topDocs['patent'] = self.filter('patent', topPatents, filterParams, 50)
        topDocs['project'] = self.filter('project', topProjects, filterParams, 15)

        expertMap, expertInfoOut = self.getSimExpertsIds(topDocs)  # 专家id为key，各项成果的相似度list为value
        # expertMap, expertInfoOut = {}, {}  # 专家id为key，各项成果的相似度list为value
        expertScoreMap = {}  # 专家为key，评分为value
        for expert in expertMap:
            expertMap[expert].sort(reverse=True)
            sim = expertMap[expert][0]
            for i in range(1, len(expertMap[expert])):
                if i >= LEN:
                    break
                sim = sim + COE * expertMap[expert][i]
            expertScoreMap[expert] = sim
        result = sorted(expertScoreMap.items(), key=lambda item: item[1], reverse=True)[0:expertTopN]
        out = []
        for i in result:
            if i[0] in expertInfoOut:
                out.append({i[0]: expertInfoOut[i[0]]})
                # out[i[0]]=expertInfoOut[i[0]]
        # self.printOut(out,LEN)
        return result

    def get_author_by_sql(self, typee, ids):
        db = DB()
        return db.getAuthors(typee, ids)  # 使用MySQL获取信息

    # 仅根据论文得到专家，由上面的most_similar_expert函数复制修改来的，以后可以重构
    def most_similar_expert_paper(self, topPapers, filterParams, expertTopN):
        file = open("config.ini", 'r')
        config = ConfigParser.ConfigParser()
        config.readfp(file)
        LEN = int(config.get('global', 'len'))  # 对于一个专家要计算多少他的成果
        COE = float(config.get('global', 'coe'))  # 对于一个专家，从第二个的成果相似度乘的系数
        topDocs = {}
        topDocs['paper'] = self.filter('paper', topPapers, filterParams, 50)
        expertMap, expertInfoOut = self.getSimExpertsIds(topDocs)  # 专家id为key，各项成果的相似度list为value
        expertScoreMap = {}  # 专家为key，评分为value
        for expert in expertMap:
            expertMap[expert].sort(reverse=True)
            sim = expertMap[expert][0]
            for i in range(1, len(expertMap[expert])):
                if i >= LEN:
                    break
                sim = sim + COE * expertMap[expert][i]
            expertScoreMap[expert] = sim
        result = sorted(expertScoreMap.items(), key=lambda item: item[1], reverse=True)[0:expertTopN]
        out = []
        for i in result:
            if i[0] in expertInfoOut:
                out.append({i[0]: expertInfoOut[i[0]]})
                # out[i[0]]=expertInfoOut[i[0]]
        # self.printOut(out,LEN)
        return result

    # 仅根据专利得到专家，由上面的most_similar_expert函数复制修改来的，以后可以重构
    def most_similar_expert_patent(self, topPatents, filterParams, expertTopN):
        file = open("config.ini", 'r')
        config = ConfigParser.ConfigParser()
        config.readfp(file)
        LEN = int(config.get('global', 'len'))  # 对于一个专家要计算多少他的成果
        COE = float(config.get('global', 'coe'))  # 对于一个专家，从第二个的成果相似度乘的系数
        topDocs = {}
        topDocs['patent'] = self.filter('patent', topPatents, filterParams, 50)
        expertMap, expertInfoOut = self.getSimExpertsIds(topDocs)  # 专家id为key，各项成果的相似度list为value
        expertScoreMap = {}  # 专家为key，评分为value
        for expert in expertMap:
            expertMap[expert].sort(reverse=True)
            sim = expertMap[expert][0]
            for i in range(1, len(expertMap[expert])):
                if i >= LEN:
                    break
                sim = sim + COE * expertMap[expert][i]
            expertScoreMap[expert] = sim
        result = sorted(expertScoreMap.items(), key=lambda item: item[1], reverse=True)[0:expertTopN]
        out = []
        for i in result:
            if i[0] in expertInfoOut:
                out.append({i[0]: expertInfoOut[i[0]]})
                # out[i[0]]=expertInfoOut[i[0]]
        # self.printOut(out,LEN)
        return result

    # 仅根据项目得到专家，由上面的most_similar_expert函数复制修改来的，以后可以重构
    def most_similar_expert_project(self, topProjects, filterParams, expertTopN):
        file = open("config.ini", 'r')
        config = ConfigParser.ConfigParser()
        config.readfp(file)
        LEN = int(config.get('global', 'len'))  # 对于一个专家要计算多少他的成果
        COE = float(config.get('global', 'coe'))  # 对于一个专家，从第二个的成果相似度乘的系数
        topDocs = {}
        topDocs['project'] = self.filter('project', topProjects, filterParams, 15)
        expertMap, expertInfoOut = self.getSimExpertsIds(topDocs)  # 专家id为key，各项成果的相似度list为value
        expertScoreMap = {}  # 专家为key，评分为value
        for expert in expertMap:
            expertMap[expert].sort(reverse=True)
            sim = expertMap[expert][0]
            for i in range(1, len(expertMap[expert])):
                if i >= LEN:
                    break
                sim = sim + COE * expertMap[expert][i]
            expertScoreMap[expert] = sim
        result = sorted(expertScoreMap.items(), key=lambda item: item[1], reverse=True)[0:expertTopN]
        out = []
        for i in result:
            if i[0] in expertInfoOut:
                out.append({i[0]: expertInfoOut[i[0]]})
                # out[i[0]]=expertInfoOut[i[0]]
        # self.printOut(out,LEN)
        return result

    def printOut(self, out, l):
        name = str('log/' + time.strftime("%Y-%m-%d %H-%M-%S" + ".txt", time.localtime()))
        print name
        output = open(name, 'w')
        for expert in out:
            for i in expert:
                list = expert[i]
                expert[i] = sorted(list, key=lambda doc: doc[1], reverse=True)[0:l]
        for expert in out:
            for i in expert:
                # print i  # 作者id
                output.write(i + '\n')
                list = expert[i]  # list为doc信息
                docOrder = ''
                for j in list:
                    docOrder = docOrder + j[0] + '                  '
                # print docOrder
                output.write(docOrder + '\n')
                sim = ''
                for j in list:
                    sim = sim + str(j[1]) + '             '
                # print sim
                output.write(sim + '\n')
                expertOrder = ''
                for j in list:
                    expertOrder = expertOrder + str(j[2]) + '                            '
                # print expertOrder
                output.write(expertOrder + '\n')
                output.write("\n")
        output.close()

    def get_model(self):
        return self.wm

    def get_cuttor(self):
        return self.cuttor
