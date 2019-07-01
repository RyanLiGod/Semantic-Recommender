#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import request
import logging.config
import utils
import json
import time

logging.config.fileConfig('logger.conf')
logger = logging.getLogger('recommServerLog')
logger.info('系统启动...')

import similarity

# import line_profiler
# from line_profiler import LineProfiler

# recmder = similarity.Recommander('/home/tdlab/recommender/data180526/wm.bin',
#                                  '/home/tdlab/recommender/data180526/ind/paper.ind',
#                                  '/home/tdlab/recommender/data180526/ind/patent.ind',
#                                  '/home/tdlab/recommender/data180526/ind/project.ind')
recmder = similarity.Recommander('/data/Recommender/data180526/wm.bin',
                                 '/data/Recommender/data180526/ind/paper.ind',
                                 '/data/Recommender/data180526/ind/patent.ind',
                                 '/data/Recommender/data180526/ind/project.ind')
TOPN = 10000  # 先取大量数据，在这数据上再做筛选，该TOPN并不是返回的数量
app = Flask(__name__)


@app.route('/recommend/cut.do')
def txt_cut():
    txt = request.args.get('txt')
    tokens = recmder.get_cuttor().fltcut(txt)
    logger.info(u'收到请求,文本：' + txt)
    return json.dumps(tokens)


@app.route('/recommend/all.do')
def get_all():
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    filterParams = []
    filterParams.append(request.args.get('field'))
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
    try:
        topPapers = recmder.most_similar_paper(txt, TOPN)
    except:
        topPapers = []
    try:
        topPatents = recmder.most_similar_patent(txt, TOPN)
    except:
        topPatents = []
    try:
        topProjects = recmder.most_similar_project(txt, TOPN)
    except:
        topProjects = []
    filteredPapers = recmder.filter('paper', topPapers, filterParams, docTopN)
    filteredPatents = recmder.filter('patent', topPatents, filterParams, docTopN)
    filteredProjects = recmder.filter('project', topProjects, filterParams, docTopN)
    experts = recmder.most_similar_expert(topPapers, topPatents, topProjects, filterParams, expertTopN)
    result = {}
    result["papers"] = [i for i, j in filteredPapers]
    result["patents"] = [i for i, j in filteredPatents]
    result["projects"] = [i for i, j in filteredProjects]
    result["experts"] = [i for i, j in experts]
    return json.dumps(result)


@app.route('/recommend/paperAndExpert.do')
def get_paperAndExpert():
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    filterParams = []
    filterParams.append(request.args.get('field'))
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
    topPapers = recmder.most_similar_paper(txt, TOPN)
    filteredPapers = recmder.filter('paper', topPapers, filterParams, docTopN)
    experts = recmder.most_similar_expert_paper(topPapers, filterParams, expertTopN)
    result = {}
    result["papers"] = [i for i, j in filteredPapers]
    result["patents"] = []
    result["projects"] = []
    result["experts"] = [i for i, j in experts]
    return json.dumps(result)


@app.route('/recommend/patentAndExpert.do')
def get_patentAndExpert():
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    filterParams = []
    filterParams.append(request.args.get('field'))
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
    topPatents = recmder.most_similar_patent(txt, TOPN)
    filteredPatents = recmder.filter('patent', topPatents, filterParams, docTopN)
    experts = recmder.most_similar_expert_patent(topPatents, filterParams, expertTopN)
    result = {}
    result["papers"] = []
    result["patents"] = [i for i, j in filteredPatents]
    result["projects"] = []
    result["experts"] = [i for i, j in experts]
    return json.dumps(result)


@app.route('/recommend/projectAndExpert.do')
def get_projectAndExpert():
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    filterParams = []
    filterParams.append(request.args.get('field'))
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
    topProjects = recmder.most_similar_project(txt, TOPN)
    filteredProjects = recmder.filter('project', topProjects, filterParams, docTopN)
    experts = recmder.most_similar_expert_project(topProjects, filterParams, expertTopN)
    result = {}
    result["papers"] = []
    result["patents"] = []
    result["projects"] = [i for i, j in filteredProjects]
    result["experts"] = [i for i, j in experts]
    return json.dumps(result)


@app.route('/recommend/expertDocsSort.do')
def get_expertDocsSort():
    txt = request.args.get('demandTxt')
    expertsIds = request.args.get('experts').strip().split(',')
    topN = int(request.args.get('topN'))
    result = {}
    for expertId in expertsIds:
        r = recmder.expertDocsSort(expertId, txt, topN)
        result[expertId] = r
    return json.dumps(result)


# @app.route('/recommend/test.do')
# def get_all():
#     txt = request.args.get('words')
#     expertTopN = int(request.args.get('expertTopN'))
#     docTopN = int(request.args.get('docTopN'))
#     filterParams = []
#     filterParams.append(request.args.get('field'))
#     filterParams.append(request.args.get('type'))
#     filterParams.append(request.args.get('province'))
#     filterParams.append(request.args.get('unit'))
#     logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
#         txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
#     topPapers = recmder.most_similar_paper(txt, TOPN)
#     topPatents = recmder.most_similar_patent(txt, TOPN)
#     topProjects = recmder.most_similar_project(txt, TOPN)
#     result = {}
#     result["papers"] = [i for i, j in topPapers][:50]
#     result["patents"] = [i for i, j in topPatents][:50]
#     result["projects"] = [i for i, j in topProjects][:50]
#     return json.dumps(result)


@app.route('/recommend/paper.do')
def get_similar_paper():
    n = int(request.args.get('docTopN'))
    txt = request.args.get('words')
    logger.info(u'#####收到请求，参数：%s,%s' % (n, txt))
    try:
        l = recmder.most_similar_paper(txt, TOPN)
    except:
        l = []
    filterParams = []
    filterParams.append(request.args.get('field'))
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append(request.args.get('journalQuality'))
    for i in range(len(filterParams)):
        if filterParams[i] == '-1':
            filterParams[i] = ''
    begin = time.time()
    l = recmder.filter('paper', l, filterParams, n)
    end = time.time()
    logger.info(u'time in filter' + str(end - begin))
    return utils.l2m_str(l)


@app.route('/recommend/patent.do')
def get_similar_patent():
    n = int(request.args.get('docTopN'))
    txt = request.args.get('words')
    logger.info(u'#####收到请求，参数：%s,%s' % (n, txt))
    try:
        l = recmder.most_similar_patent(txt, TOPN)
    except:
        l = []
    filterParams = []
    filterParams.append(request.args.get('field'))
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append(request.args.get('patentType'))
    for i in range(len(filterParams)):
        if filterParams[i] == '-1':
            filterParams[i] = ''
    begin = time.time()
    l = recmder.filter('patent', l, filterParams, n)
    end = time.time()
    logger.info(u'time in filter' + str(end - begin))
    return utils.l2m_str(l)


@app.route('/recommend/project.do')
def get_similar_project():
    n = int(request.args.get('docTopN'))
    txt = request.args.get('words')
    try:
        l = recmder.most_similar_project(txt, TOPN)
    except:
        l = []
    filterParams = []
    filterParams.append('Z9')
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append(request.args.get('projectType'))
    for i in range(len(filterParams)):
        if filterParams[i] == '-1':
            filterParams[i] = ''
    begin = time.time()
    l = recmder.filter('project', l, filterParams, n)
    end = time.time()
    logger.info(u'time in filter' + str(end - begin))
    return utils.l2m_str(l)


@app.route('/recommend/expert.do')
def get_expert():
    n = int(request.args.get('topN'))
    txt = request.args.get('words')
    filterParams = []
    filterParams.append(request.args.get('field'))
    filterParams.append(request.args.get('type'))
    filterParams.append(request.args.get('province'))
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    for i in range(len(filterParams)):
        if filterParams[i] == '-1':
            filterParams[i] = ''
    begin = time.time()
    map = {}
    l = recmder.most_similar_paper(txt, 10000)
    l = recmder.filter('paper', l, filterParams, 50)
    map['paper'] = l
    l = recmder.most_similar_patent(txt, 10000)
    l = recmder.filter('patent', l, filterParams, 50)
    map['patent'] = l
    l = recmder.most_similar_project(txt, 10000)
    l = recmder.filter('project', l, filterParams, 15)
    map['project'] = l
    experts = recmder.most_similar_expert(txt, map)
    end = time.time()
    logger.info(u'time in get experts' + str(end - begin))
    result = experts[0:n]
    result = utils.l2m_str(result)
    return result


@app.route('/analysis/is_contain.do')
def is_contain():
    w = request.args.get('w')
    wm = recmder.get_model()
    return json.dumps(w in wm)


@app.route('/analysis/topnwords.do')
def topnwords():
    try:
        n = int(request.args.get('n'))
        w = request.args.get('w')
        logger.info(u'#####收到请求，参数：%s,%s' % (n, w))
        r = recmder.get_model().most_similar(w, topn=n)
        l = [w for w, s in r]
    except:
        l = []
    return json.dumps(l)


@app.route('/analysis/docscontainword.do')
def docs_contain_word():
    w = request.args.get('w')
    c = request.args.get('c')
    return 'unimplemented yet!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8640)
