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

# recmder = similarity.Recommander('/home/tdlab/recommender/data_filter/wm.bin',
#                                  '/home/tdlab/recommender/data_filter/ind/paper/',
#                                  '/home/tdlab/recommender/data_filter/ind/patent/',
#                                  '/home/tdlab/recommender/data_filter/ind/project/')
recmder = similarity.Recommander('/data/Recommender/data_filter/wm.bin',
                                 '/data/Recommender/data_filter/ind/paper/',
                                 '/data/Recommender/data_filter/ind/patent/',
                                 '/data/Recommender/data_filter/ind/project/')
TOPN = 50  # 先取大量数据，在这数据上再做筛选，该TOPN并不是返回的数量
app = Flask(__name__)


@app.route('/recommend/cut.do')
def txt_cut():
    txt = request.args.get('txt')
    tokens = recmder.get_cuttor().fltcut(txt)
    logger.info(u'收到请求,文本：' + txt)
    return json.dumps(tokens)


@app.route('/recommend/all.do')
def get_all():
    begin = time.time()
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    unit_type = request.args.get('type')
    province = request.args.get('province')
    field = request.args.get('field')
    # filterParams = []
    # filterParams.append(field)
    # filterParams.append(unit_type)
    # filterParams.append(province)
    # filterParams.append(request.args.get('unit'))
    # filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, field, unit_type, province, request.args.get('unit')))
    ann_1 = time.time()
    topPapers = recmder.most_similar_paper(txt, TOPN, field, unit_type, province)
    ann_2 = time.time()
    topPatents = recmder.most_similar_patent(txt, TOPN, field, unit_type, province)
    ann_3 = time.time()
    topProjects = recmder.most_similar_project(txt, TOPN, 'Z9', unit_type, province)
    ann_4 = time.time()
    logger.info(u'time in ann' + str(ann_4 - ann_1))
    logger.info(u'time in paper ann' + str(ann_2 - ann_1))
    logger.info(u'time in patent ann' + str(ann_3 - ann_2))
    logger.info(u'time in project ann' + str(ann_4 - ann_3))
    # filteredPapers = recmder.filter('paper', topPapers, filterParams, docTopN)
    # filteredPatents = recmder.filter('patent', topPatents, filterParams, docTopN)
    # filteredProjects = recmder.filter('project', topProjects, filterParams, docTopN)
    expert_1 = time.time()
    experts = recmder.most_similar_expert(topPapers[0:40], topPatents[0:40], topProjects[0:20], [], expertTopN)
    expert_2 = time.time()
    logger.info(u'time in 拼人' + str(expert_2 - expert_1))
    result = {}
    result["papers"] = [i for i, j in topPapers[0:docTopN]]
    result["patents"] = [i for i, j in topPatents[0:docTopN]]
    result["projects"] = [i for i, j in topProjects[0:docTopN]]
    result["experts"] = [i for i, j in experts]
    end = time.time()
    logger.info(u'time in total' + str(end - begin))
    return json.dumps(result)


@app.route('/recommend/paperAndExpert.do')
def get_paperAndExpert():
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    unit_type = request.args.get('type')
    province = request.args.get('province')
    field = request.args.get('field')
    filterParams = []
    filterParams.append(field)
    filterParams.append(unit_type)
    filterParams.append(province)
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
    topPapers = recmder.most_similar_paper(txt, TOPN, field, unit_type, province)
    # filteredPapers = recmder.filter('paper', topPapers, filterParams, docTopN)
    experts = recmder.most_similar_expert_paper(topPapers[0:80], filterParams, expertTopN)
    result = {}
    result["papers"] = [i for i, j in topPapers[0:docTopN]]
    result["patents"] = []
    result["projects"] = []
    result["experts"] = [i for i, j in experts]
    return json.dumps(result)


@app.route('/recommend/patentAndExpert.do')
def get_patentAndExpert():
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    unit_type = request.args.get('type')
    province = request.args.get('province')
    field = request.args.get('field')
    filterParams = []
    filterParams.append(field)
    filterParams.append(unit_type)
    filterParams.append(province)
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
    topPatents = recmder.most_similar_patent(txt, TOPN, field, unit_type, province)
    # filteredPatents = recmder.filter('patent', topPatents, filterParams, docTopN)
    experts = recmder.most_similar_expert_patent(topPatents[0:80], filterParams, expertTopN)
    result = {}
    result["papers"] = []
    result["patents"] = [i for i, j in topPatents[0:docTopN]]
    result["projects"] = []
    result["experts"] = [i for i, j in experts]
    return json.dumps(result)


@app.route('/recommend/projectAndExpert.do')
def get_projectAndExpert():
    txt = request.args.get('words')
    expertTopN = int(request.args.get('expertTopN'))
    docTopN = int(request.args.get('docTopN'))
    unit_type = request.args.get('type')
    province = request.args.get('province')
    field = request.args.get('field')
    filterParams = []
    filterParams.append(field)
    filterParams.append(unit_type)
    filterParams.append(province)
    filterParams.append(request.args.get('unit'))
    filterParams.append('-1')
    logger.info(u'#####收到请求，参数：txt=%s,field=%s,type=%s,province=%s,unit=%s' % (
        txt, filterParams[0], filterParams[1], filterParams[2], filterParams[3]))
    topProjects = recmder.most_similar_project(txt, TOPN, 'Z9', unit_type, province)
    # filteredProjects = recmder.filter('project', topProjects, filterParams, docTopN)
    experts = recmder.most_similar_expert_project(topProjects[0:80], filterParams, expertTopN)
    result = {}
    result["papers"] = []
    result["patents"] = []
    result["projects"] = [i for i, j in topProjects[0:docTopN]]
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
    unit_type = request.args.get('type')
    province = request.args.get('province')
    field = request.args.get('field')
    try:
        l = recmder.most_similar_paper(txt, TOPN, field, unit_type, province)
    except:
        l = []
    filterParams = []
    filterParams.append(field)
    filterParams.append(unit_type)
    filterParams.append(province)
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
    unit_type = request.args.get('type')
    province = request.args.get('province')
    field = request.args.get('field')
    try:
        l = recmder.most_similar_patent(txt, TOPN, field, unit_type, province)
    except:
        l = []
    filterParams = []
    filterParams.append(field)
    filterParams.append(unit_type)
    filterParams.append(province)
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
    unit_type = request.args.get('type')
    province = request.args.get('province')
    try:
        l = recmder.most_similar_project(txt, TOPN, 'Z9', unit_type, province)
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
    expertTopN = int(request.args.get('expertTopN'))
    txt = request.args.get('words')
    unit_type = request.args.get('type')
    province = request.args.get('province')
    field = request.args.get('field')
    # filterParams = []
    # filterParams.append(field)
    # filterParams.append(unit_type)
    # filterParams.append(province)
    # filterParams.append(request.args.get('unit'))
    # filterParams.append('-1')
    # for i in range(len(filterParams)):
    #     if filterParams[i] == '-1':
    #         filterParams[i] = ''
    begin = time.time()
    topPapers = recmder.most_similar_paper(txt, TOPN, field, unit_type, province)
    topPatents = recmder.most_similar_patent(txt, TOPN, field, unit_type, province)
    topProjects = recmder.most_similar_project(txt, TOPN, 'Z9', unit_type, province)
    experts = recmder.most_similar_expert(topPapers[0:80], topPatents[0:80], topProjects[0:30], [], expertTopN)
    end = time.time()
    logger.info(u'time in get experts' + str(end - begin))
    return utils.l2m_str(experts)


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
