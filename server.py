#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
import tornado.httpserver
import logging.config
import utils
import json
import time

logging.config.fileConfig('logger.conf')
logger = logging.getLogger('recommServerLog')
logger.info('系统启动...')

import similarity

if utils.get_host_ip() == '10.1.13.49':
    recmder = similarity.Recommander('/home/tdlab/recommender/data_hnsw/wm.bin',
                                     '/home/tdlab/recommender/data_hnsw/ind/paper.ind',
                                     '/home/tdlab/recommender/data_hnsw/ind/patent.ind',
                                     '/home/tdlab/recommender/data_hnsw/ind/project.ind')
else:
    recmder = similarity.Recommander('/data/Recommender/data_hnsw/wm.bin',
                                     '/data/Recommender/data_hnsw/ind/paper.ind',
                                     '/data/Recommender/data_hnsw/ind/patent.ind',
                                     '/data/Recommender/data_hnsw/ind/project.ind')
TOPN = 10000  # 先取大量数据，在这数据上再做筛选，该TOPN并不是返回的数量
TOPN_project = 1000
ef_paper = TOPN
ef_patent = TOPN
ef_project = TOPN_project

# /recommend/all.do
class AllHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())
    @run_on_executor
    def get(self):
        begin = time.time()
        txt = self.get_query_argument('words')
        expertTopN = int(self.get_query_argument('expertTopN'))
        docTopN = int(self.get_query_argument('docTopN'))
        unit_type = self.get_query_argument('type')
        province = self.get_query_argument('province')
        field = self.get_query_argument('field')
        unit = self.get_query_argument('unit')

        # try:
        #     TOPN = int(self.get_query_argument('TOPN'))
        #     TOPN_project = int(self.get_query_argument('TOPN_project'))
        #     ef_paper = int(self.get_query_argument('ef_paper'))
        #     ef_patent = int(self.get_query_argument('ef_patent'))
        #     ef_project = int(self.get_query_argument('ef_project'))
        # except Exception:
        #     TOPN = 10000  # 先取大量数据，在这数据上再做筛选，该TOPN并不是返回的数量
        #     TOPN_project = 1000
        #     ef_paper = TOPN
        #     ef_patent = TOPN
        #     ef_project = 1000
        recmder.set_ef('paper', ef_paper)
        recmder.set_ef('patent', ef_patent)
        recmder.set_ef('project', ef_project)

        filterParams = [field, unit_type, province, unit, '-1']
        logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
            txt, field, unit_type, province, unit))
        ann_1 = time.time()
        topPapers = recmder.most_similar_paper(txt, TOPN)
        logger.info(u'length of paper: ' + str(len(topPapers)))
        ann_2 = time.time()
        topPatents = recmder.most_similar_patent(txt, TOPN)
        logger.info(u'length of patent: ' + str(len(topPatents)))
        ann_3 = time.time()
        topProjects = recmder.most_similar_project(txt, TOPN_project)
        logger.info(u'length of project: ' + str(len(topProjects)))
        ann_4 = time.time()
        logger.info(u'time in ann ' + str(ann_4 - ann_1))
        logger.info(u'time in paper ann ' + str(ann_2 - ann_1))
        logger.info(u'time in patent ann ' + str(ann_3 - ann_2))
        logger.info(u'time in project ann ' + str(ann_4 - ann_3))

        filteredPapers = recmder.filter('paper', topPapers, filterParams, docTopN)
        filteredPatents = recmder.filter('patent', topPatents, filterParams, docTopN)
        filteredProjects = recmder.filter('project', topProjects, filterParams, docTopN)
        
        filter_time = time.time()
        logger.info(u'time in filter' + str(filter_time - ann_4))
        expert_1 = time.time()

        logger.info(u'length of filteredPapers: ' + str(len(filteredPapers)))
        logger.info(u'length of filteredPatents: ' + str(len(filteredPatents)))
        logger.info(u'length of filteredProjects: ' + str(len(filteredProjects)))

        experts = recmder.most_similar_expert(topPapers, topPatents, topProjects, filterParams, expertTopN)
        expert_2 = time.time()
        logger.info(u'time in 拼人' + str(expert_2 - expert_1))
        result = {}
        result["papers"] = [i for i, j in filteredPapers[0:docTopN]]
        result["patents"] = [i for i, j in filteredPatents[0:docTopN]]
        result["projects"] = [i for i, j in filteredProjects[0:docTopN]]
        result["experts"] = [i for i, j in experts]
        end = time.time()
        logger.info(u'time in total ' + str(end - begin))
        self.write(json.dumps(result))


# /recommend/paper.do
class PaperHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        n = int(self.get_query_argument('docTopN'))
        txt = self.get_query_argument('words')
        logger.info(u'#####收到请求，参数：%s,%s' % (n, txt))
        unit_type = self.get_query_argument('type')
        province = self.get_query_argument('province')
        field = self.get_query_argument('field')
        unit = self.get_query_argument('unit')
        journalQuality = self.get_query_argument('journalQuality')
        
        recmder.set_ef('paper', ef_paper)
        recmder.set_ef('patent', ef_patent)
        recmder.set_ef('project', ef_project)
        
        try:
            ann_time = time.time()
            l = recmder.most_similar_paper(txt, TOPN)
            logger.info(u'time in paper ann ' + str(time.time() - ann_time))
        except:
            l = []
        filterParams = [field, unit_type, province, unit, journalQuality]
        begin = time.time()
        l = recmder.filter('paper', l, filterParams, n)
        end = time.time()
        logger.info(u'time in filter ' + str(end - begin))
        self.write(utils.l2m_str(l))


# /recommend/patent.do
class PatentHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        n = int(self.get_query_argument('docTopN'))
        txt = self.get_query_argument('words')
        logger.info(u'#####收到请求，参数：%s,%s' % (n, txt))
        unit_type = self.get_query_argument('type')
        province = self.get_query_argument('province')
        field = self.get_query_argument('field')
        unit = self.get_query_argument('unit')
        patentType = self.get_query_argument('patentType')
        try:
            ann_time = time.time()
            l = recmder.most_similar_patent(txt, TOPN)
            logger.info(u'time in patent ann ' + str(time.time() - ann_time))
        except:
            l = []
        filterParams = [field, unit_type, province, unit, patentType]
        for i in range(len(filterParams)):
            if filterParams[i] == '-1':
                filterParams[i] = ''
        begin = time.time()
        l = recmder.filter('patent', l, filterParams, n)
        end = time.time()
        logger.info(u'time in filter' + str(end - begin))
        self.write(utils.l2m_str(l))


# /recommend/project.do
class ProjectHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        n = int(self.get_query_argument('docTopN'))
        txt = self.get_query_argument('words')
        unit_type = self.get_query_argument('type')
        province = self.get_query_argument('province')
        unit = self.get_query_argument('unit')
        projectType = self.get_query_argument('projectType')
        try:
            ann_time = time.time()
            l = recmder.most_similar_project(txt, TOPN_project)
            logger.info(u'time in project ann ' + str(time.time() - ann_time))
        except:
            l = []
        filterParams = ['Z9', unit_type, province, unit, projectType]
        for i in range(len(filterParams)):
            if filterParams[i] == '-1':
                filterParams[i] = ''
        begin = time.time()
        l = recmder.filter('project', l, filterParams, n)
        end = time.time()
        logger.info(u'time in filter' + str(end - begin))
        self.write(utils.l2m_str(l))


# /recommend/paperAndExpert.do
class PaperAndExpertHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        txt = self.get_query_argument('words')
        expertTopN = int(self.get_query_argument('expertTopN'))
        docTopN = int(self.get_query_argument('docTopN'))
        unit_type = self.get_query_argument('type')
        province = self.get_query_argument('province')
        field = self.get_query_argument('field')
        filterParams = []
        filterParams.append(field)
        filterParams.append(unit_type)
        filterParams.append(province)
        filterParams.append(self.get_query_argument('unit'))
        filterParams.append('-1')
        logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
            txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
        topPapers = recmder.most_similar_paper(txt, TOPN)
        filteredPapers = recmder.filter('paper', topPapers, filterParams, docTopN)
        experts = recmder.most_similar_expert_paper(filteredPapers[0:80], filterParams, expertTopN)
        result = {}
        result["papers"] = [i for i, j in filteredPapers[0:docTopN]]
        result["patents"] = []
        result["projects"] = []
        result["experts"] = [i for i, j in experts]
        self.write(json.dumps(result))


# /recommend/patentAndExpert.do
class PatentAndExpertHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        txt = self.get_query_argument('words')
        expertTopN = int(self.get_query_argument('expertTopN'))
        docTopN = int(self.get_query_argument('docTopN'))
        unit_type = self.get_query_argument('type')
        province = self.get_query_argument('province')
        field = self.get_query_argument('field')
        filterParams = []
        filterParams.append(field)
        filterParams.append(unit_type)
        filterParams.append(province)
        filterParams.append(self.get_query_argument('unit'))
        filterParams.append('-1')
        logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
            txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
        topPatents = recmder.most_similar_patent( txt, TOPN)
        filteredPatents = recmder.filter('patent', topPatents, filterParams, docTopN)
        experts = recmder.most_similar_expert_patent(filteredPatents[0:80], filterParams, expertTopN)
        result = {}
        result["papers"] = []
        result["patents"] = [i for i, j in filteredPatents[0:docTopN]]
        result["projects"] = []
        result["experts"] = [i for i, j in experts]
        self.write(json.dumps(result))


# /recommend/projectAndExpert.do
class ProjectAndExpertHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        txt = self.get_query_argument('words')
        expertTopN = int(self.get_query_argument('expertTopN'))
        docTopN = int(self.get_query_argument('docTopN'))
        unit_type = self.get_query_argument('type')
        province = self.get_query_argument('province')
        field = self.get_query_argument('field')
        filterParams = []
        filterParams.append(field)
        filterParams.append(unit_type)
        filterParams.append(province)
        filterParams.append(self.get_query_argument('unit'))
        filterParams.append('-1')
        logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
            txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
        TOPN = 1000
        topProjects = recmder.most_similar_project(txt, TOPN)
        filteredProjects = recmder.filter('project', topProjects, filterParams, docTopN)
        experts = recmder.most_similar_expert_project(filteredProjects[0:80], filterParams, expertTopN)
        result = {}
        result["papers"] = []
        result["patents"] = []
        result["projects"] = [i for i, j in filteredProjects[0:docTopN]]
        result["experts"] = [i for i, j in experts]
        self.write(json.dumps(result))


# /recommend/cut.do
class CutHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        txt = self.get_query_argument('txt')
        tokens = recmder.get_cuttor().fltcut(txt)
        logger.info(u'收到请求,文本：' + txt)
        self.write(json.dumps(tokens))


# /recommend/expertDocsSort.do
class ExpertDocsHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        txt = self.get_query_argument('demandTxt')
        expertsIds = self.get_query_argument('experts').strip().split(',')
        topN = int(self.get_query_argument('topN'))
        result = {}
        for expertId in expertsIds:
            r = recmder.expertDocsSort(expertId, txt, topN)
            result[expertId] = r
        self.write(json.dumps(result))


# /recommend/is_contain.do
class ContainHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        w = self.get_query_argument('w')
        wm = recmder.get_model()
        self.write(json.dumps(w in wm))


# /recommend/topnwords.do
class TopWordHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(cpu_count())

    @run_on_executor
    def get(self):
        try:
            n = int(self.get_query_argument('n'))
            w = self.get_query_argument('w')
            logger.info(u'#####收到请求，参数：%s,%s' % (n, w))
            r = recmder.get_model().most_similar(w, topn=n)
            l = [w for w, s in r]
        except:
            l = []
        self.write(json.dumps(l))


def make_app():
    return tornado.web.Application([
        tornado.web.url(r"/recommend/all.do", AllHandler),
        tornado.web.url(r"/recommend/paper.do", PaperHandler),
        tornado.web.url(r"/recommend/patent.do", PatentHandler),
        tornado.web.url(r"/recommend/project.do", ProjectHandler),
        tornado.web.url(r"/recommend/paperAndExpert.do", PaperAndExpertHandler),
        tornado.web.url(r"/recommend/patentAndExpert.do", PatentAndExpertHandler),
        tornado.web.url(r"/recommend/projectAndExpert.do", ProjectAndExpertHandler),
        tornado.web.url(r"/recommend/expertDocsSort.do", ExpertDocsHandler),
        tornado.web.url(r"/recommend/cut.do", CutHandler),
        tornado.web.url(r"/analysis/is_contain.do", ContainHandler),
        tornado.web.url(r"/analysis/topnwords.do", TopWordHandler),
    ])


if __name__ == '__main__':
    logger.info(u'Number of threads: %s' % cpu_count())
    app = make_app()
    app.listen(8640)
    logger.info(u'Server run on port 8640')
    tornado.ioloop.IOLoop.current().start()
