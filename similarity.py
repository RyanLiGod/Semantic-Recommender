#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Pyro4
from numpy import array
import gensim
import os
import codecs
from mycut import FilterCut
from corpora import CorporaWithTitle
from gensim.similarities.index import AnnoyIndexer
from DBUtil import DB
import time
import ConfigParser
from annoy import AnnoyIndex


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
    def __init__(self):
        # self.wm = gensim.models.KeyedVectors.load_word2vec_format(vec_file,binary=True)
        # vec_file = '/home/tdlab/recommender/data180302/wm.bin'
        # pap = '/home/tdlab/recommender/data180302/ind/paper.ind'
        # pat = '/home/tdlab/recommender/data180302/ind/patent.ind'
        # pro = '/home/tdlab/recommender/data180302/ind/project.ind'
        vec_file = '/root/recommender/data180302/wm.bin'
        pap = '/root/recommender/data180302/ind/paper.ind'
        pat = '/root/recommender/data180302/ind/patent.ind'
        pro = '/root/recommender/data180302/ind/project.ind'
        self.wm = gensim.models.word2vec.Word2Vec.load_word2vec_format(vec_file, binary=True)
        self.paper_index = AnnoyIndexer()
        self.paper_index.load(pap)
        self.patent_index = AnnoyIndexer()
        self.patent_index.load(pat)
        self.project_index = AnnoyIndexer()
        self.project_index.load(pro)
        self.t2v = Convert2Vec(self.wm)
        self.cuttor = FilterCut()
        self.db = DB()
        self.featureIndex = self.buildFeatureIndex()

    def buildFeatureIndex(self):
        # paperFeature = open("/home/tdlab/recommender/data180302/feature/paper_feature180420.txt", 'r')
        # patentFeature = open("/home/tdlab/recommender/data180302/feature/patent_feature180420.txt", 'r')
        # projectFeature = open("/home/tdlab/recommender/data180302/feature/project_feature180420.txt", 'r')
        paperFeature = open("/root/recommender/data180302/feature/paper_feature180420.txt", 'r')
        patentFeature = open("/root/recommender/data180302/feature/patent_feature180420.txt", 'r')
        projectFeature = open("/root/recommender/data180302/feature/project_feature180420.txt", 'r')
        featureIndex = {}
        featureIndex['paper'] = self.loadFeature(paperFeature, 'paper')
        featureIndex['patent'] = self.loadFeature(patentFeature, 'patent')
        featureIndex['project'] = self.loadFeature(projectFeature, 'project')
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
            if feature[1] not in index['field']:
                index['field'][feature[1]] = []
            index['field'][feature[1]].append(feature[0])
            if feature[2] not in index['type']:
                index['type'][feature[2]] = []
            index['type'][feature[2]].append(feature[0])
            if feature[3] not in index['province']:
                index['province'][feature[3]] = []
            index['province'][feature[3]].append(feature[0])
            if feature[4] not in index['unit']:
                index['unit'][feature[4]] = []
            index['unit'][feature[4]].append(feature[0])
            if typee == 'paper':
                if feature[7] not in index['journalQuality']:
                    index['journalQuality'][feature[7]] = []
                index['journalQuality'][feature[7]].append(feature[0])
            if typee == 'patent':
                if feature[7] not in index['patentType']:
                    index['patentType'][feature[7]] = []
                index['patentType'][feature[7]].append(feature[0])
            if typee == 'project':
                if feature[7] not in index['projectType']:
                    index['projectType'][feature[7]] = []
                index['projectType'][feature[7]].append(feature[0])
        return index

    # 获取某专家的所有成果对于需求txt的按相似度排序，论文专利项目分别返回前topN
    def expertDocsSort(self, expertId, txt, topN):
        vec = self.t2v.text2v(txt, self.cuttor)
        annoy = AnnoyIndex(200)

        count = 0
        annoy.add_item(count, vec)
        count = count + 1
        papers = self.db.getPapers(expertId)
        for p in papers:
            p[3] = self.t2v.text2v(p[1] + p[2], self.cuttor)
            annoy.add_item(count, p[3])
            p[3] = annoy.get_distance(0, count)
            count = count + 1
        papers = sorted(papers, key=lambda p: p[3])
        papersFormated = []
        for p in papers:
            if len(papersFormated) == topN:
                break
            map = {}
            map['paperId'] = p[0]
            map['name'] = p[1]
            map['authors'] = p[4]
            map['journalName'] = p[5]
            map['year'] = p[6]
            papersFormated.append(map)

        count = 0
        annoy.unload()
        annoy.add_item(count, vec)
        count = count + 1
        patents = self.db.getPatents(expertId)
        for p in patents:
            p[3] = self.t2v.text2v(p[1] + p[2], self.cuttor)
            annoy.add_item(count, p[3])
            p[3] = annoy.get_distance(0, count)
            count = count + 1
        patents = sorted(patents, key=lambda p: p[3])
        patentsFormated = []
        for p in patents:
            if len(patentsFormated) == topN:
                break
            map = {}
            map['patentId'] = p[0]
            map['publicationNo'] = p[4]
            map['name'] = p[1]
            map['inventors'] = p[5]
            map['applicant'] = p[6]
            map['year'] = p[7]
            patentsFormated.append(map)

        count = 0
        annoy.unload()
        annoy.add_item(count, vec)
        count = count + 1
        projects = self.db.getProjects(expertId)
        for p in projects:
            p[3] = self.t2v.text2v(p[1] + p[2], self.cuttor)
            annoy.add_item(count, p[3])
            p[3] = annoy.get_distance(0, count)
            count = count + 1
        projects = sorted(projects, key=lambda p: p[3])
        projectsFormated = []
        for p in projects:
            if len(projectsFormated) == topN:
                break
            map = {}
            map['projectId'] = p[0]
            map['name'] = p[1]
            map['member'] = p[4]
            map['unit'] = p[5]
            map['year'] = p[6]
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
        for typee in topDocs:
            order = {}
            order[typee] = {}
            k = 0
            for i, j in topDocs[typee]:
                order[typee][i] = k
                k = k + 1
            ids = [i for i, j in topDocs[typee]]
            docExpertIds = self.db.getAuthors(typee, ids)
            for id in docExpertIds:
                if not self.db.idInDB(typee, id):
                    print "docId:" + id + "is not in db"
                    continue
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
                    if expertIds[i] not in expertInfoOut:
                        expertInfoOut[expertIds[i]] = []
                    expertInfoOut[expertIds[i]].append([typee + str(order[typee][id]), sim * authorSeqWeiht[i], i])
                    if expertIds[i] not in expertMap:
                        expertMap[expertIds[i]] = []
                    expertMap[expertIds[i]].append(sim * authorSeqWeiht[i])
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

        # lp = LineProfiler()
        # lp_wrapper = lp(self.getSimExpertsIds)
        # expertMap, expertInfoOut = lp_wrapper(topDocs)
        # lp.print_stats()

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


@Pyro4.expose
class Pyro4Expose(object):
    def expertDocsSort(self, expertId, txt, topN):
        return recommander.expertDocsSort(expertId, txt, topN)

    def filter(self, typee, topDocs, filterParams, topN):
        return recommander.filter(typee, topDocs, filterParams, topN)

    def most_similar_paper(self, text, topn):
        return recommander.most_similar_paper(text, topn)

    def most_similar_patent(self, text, topn):
        return recommander.most_similar_patent(text, topn)

    def most_similar_project(self, text, topn):
        return recommander.most_similar_project(text, topn)

    def getSimExpertsIds(self, topDocs):
        return recommander.getSimExpertsIds(topDocs)

    def most_similar_expert(self, topPapers, topPatents, topProjects, filterParams, expertTopN):
        return recommander.most_similar_expert(topPapers, topPatents, topProjects, filterParams, expertTopN)

    def most_similar_expert_paper(self, topPapers, filterParams, expertTopN):
        return recommander.most_similar_expert_paper(topPapers, filterParams, expertTopN)

    def most_similar_expert_patent(self, topPatents, filterParams, expertTopN):
        return recommander.most_similar_expert_patent(topPatents, filterParams, expertTopN)

    def most_similar_expert_project(self, topProjects, filterParams, expertTopN):
        return recommander.most_similar_expert_project(topProjects, filterParams, expertTopN)

    def printOut(self, out, l):
        return recommander.printOut(out, l)

    def get_model(self):
        return recommander.get_model()

    def get_cuttor(self):
        return recommander.get_cuttor()


if __name__ == '__main__':
    recommander = Recommander()
    daemon = Pyro4.Daemon()  # make a Pyro daemon
    ns = Pyro4.locateNS()  # find the name server
    uri = daemon.register(Pyro4Expose)  # register the greeting maker as a Pyro object
    ns.register("similarity.server", uri)  # register the object with a name in the name server

    print "Similarity Server Ready."
    daemon.requestLoop()
