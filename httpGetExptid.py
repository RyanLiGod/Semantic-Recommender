#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import logging
import re
import logTime
import codecs
import logging.config
#搜索引擎地址
SOLR_SERVER = 'http://10.1.13.75:8983/solr'
URL_FORMAT = u'%s/%s/select'
#查询返回的条目数
QUERY_COUNT = 100

logging.config.fileConfig('logger.conf')
logger = logging.getLogger()

def solrQuery(catagory,queryTxt):
    queryUrl = URL_FORMAT % (SOLR_SERVER,catagory)
    form_data = {'rows':QUERY_COUNT,'wt':'json','q':queryTxt}
    r = requests.post(queryUrl,data=form_data)
    #r = requests.get(queryUrl,data=form_data)
    return r.text

@logTime.log_time
def getJsonData(catagory,queryTxt):
    logger.debug(u'获取%s数据,查询文本:%s' % (catagory,queryTxt))
    resp = solrQuery(catagory,queryTxt)
    try:
        jsonResp = json.loads(resp)
    except Exception,e:
        logger.error(e.message)
        return []
    if (u'responseHeader' in jsonResp) and (u'status' in jsonResp[u'responseHeader']) and (jsonResp[u'responseHeader'][u'status'] == 0):
        return jsonResp[u'response'][u'docs']
    else:
        logger.error(u'request faild.response body:%s' % resp[:200])
    return []

@logTime.log_time
def parse(jsonData,parser):
    r = []
    for obj in jsonData:
        del obj[u'_version_']
        r.append(parser(obj))
    return r

#def getExperts(queryTxt):
#    jsonData = getJsonData('expert',queryTxt)
#    parser = lambda obj: {'id':obj.pop('id'),\
#            'name':obj.pop('name'),\
#            'txt':' '.join(obj.values())} 
#    return parse(jsonData,parser)

def getProjects(queryTxt):
    jsonData = getJsonData('project',queryTxt)
    parser = lambda obj: {'id':obj.pop(u'id'),\
            'eid':obj[u'EXPERT_ID'],\
            'name':obj[u'name'],\
            'txt':' '.join((obj[u'name'],obj[u'keywords_ch'],obj[u'abstract_ch']))}
    return parse(jsonData,parser)

def getPapers(queryTxt):
    jsonData = getJsonData('paper',queryTxt)
    parser = lambda obj: {'id':obj.pop(u'id'),\
            'eid':obj[u'EXPERT_ID'],\
            'name':obj[u'name'],\
            'txt':' '.join((obj[u'name'],obj[u'abstract'],obj[u'keywords']))}
    return parse(jsonData,parser)

def getPatents(queryTxt):
    jsonData = getJsonData('patent',queryTxt)
    parser = lambda obj: {'id':obj.pop(u'id'),\
            'eid':obj[u'EXPERT_ID'],\
            'name':obj[u'name'],\
            'txt':' '.join((obj[u'name'],obj[u'abstract']))}
    return parse(jsonData,parser)

def getExperts(queryTxt):
    papers = getPapers(queryTxt)
    patents = getPatents(queryTxt)
    projects = getProjects(queryTxt)
    experts = [{'id':e[u'eid'],'txt':e[u'txt']} for e in (papers + patents + projects)]
    return experts

if __name__ == '__main__':

    txt = u'相关文档'
    print getExperts(txt)

   # dataFileName = './data/patent_concat.txt'
   # dataFile = codecs.open(dataFileName,'r','utf-8')
   # lineCount = -1
   # offset = 2000
   # for line in dataFile:
   #     lineCount += 1
   #     if lineCount < offset:
   #         continue
   #     cols = line.strip().split(',')
   #     print cols[0]
   #     doc = u' '.join(cols[1:])
   #     r= getPatents(doc[:3000])
   #     l = [e['name'] for e in r]
   #     print ' '.join(l)
   #     break
