#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
连接MySQL数据库，是Redis的备用方案，在Redis失效的时候使用。
'''

import MySQLdb
import time
from redis_util import RedisUtil
import logging.config
import utils

logging.config.fileConfig('logger.conf')
logger = logging.getLogger('recommServerLog')


class DB(object):

    def __init__(self):
        if utils.get_host_ip() == '10.1.13.49':
            self.HOST = '10.1.13.29'
        else:
            self.HOST = '202.107.204.50'
        self.conn = MySQLdb.connect(host=self.HOST, user='root', passwd='tdlabDatabase', db='techpooldata',
                                    port=3306, charset='utf8')
        self.tables = {'paper': 'expert_paper_join', 'patent': 'expert_patent_join', 'project': 'expert_project_join'}
        self.columns = {'paper': 'PAPER_ID', 'patent': 'PATENT_ID', 'project': 'PROJECT_ID'}
        self.redis = RedisUtil()

    def getConnection(self):
        try:
            self.conn.ping()
        except:
            self.conn = MySQLdb.connect(host=self.HOST, user='root', passwd='tdlabDatabase', db='techpooldata',
                                        port=3306, charset='utf8')
            print 'reconnection'
        return self.conn

    # 返回以docId为key，以authors为value的map
    def getAuthors(self, typee, ids):
        begin = time.time()
        if len(ids) == 0:
            return {}
        authorIds = {}
        sql = "select " + self.columns[typee] + ",EXPERT_ID from " + self.tables[typee] + " where " + self.columns[
            typee] + " in("
        for i in range(len(ids)):
            sql = sql + "'" + ids[i] + "'"
            if i != len(ids) - 1:
                sql = sql + ','
        sql = sql + ') order by ' + self.columns[typee] + ',expert_role'
        cur = self.getConnection().cursor()
        cur.execute(sql)
        results = cur.fetchall()
        cur.close()
        for line in results:
            if line[0] not in authorIds:
                authorIds[line[0]] = []
            authorIds[line[0]].append(line[1])
        end = time.time()
        print '############# time in ' + typee + ' getAuthors()' + str(end - begin)
        return authorIds

    # 返回id是否在数据库中，因为有时数据不同步
    def idInDB(self, typee, id):
        cur = self.getConnection().cursor()
        sql = "select * from " + self.tables[typee] + " where " + self.columns[typee] + " ='" + id + "'"
        count = cur.execute(sql)
        cur.close()
        return count > 0

    # 返回一个作者的论文，包括非第一作者
    def getPapers(self, expertId):
        sql = "select p.PAPER_ID, p.name, p.abstract,p.authors, p.journal_name, p.year from expert_paper_join j JOIN paper p on j.PAPER_ID=p.PAPER_ID where j.EXPERT_ID='" + expertId + "';"
        cur = self.getConnection().cursor()
        cur.execute(sql)
        r = cur.fetchall()
        result = []
        for line in r:
            if line[2] is None:
                abstract = ''
            else:
                abstract = line[2]
            result.append([line[0], line[1], abstract, None, line[3], line[4], line[5]])
        return result

    # 返回一个作者的专利，包括非第一作者
    def getPatents(self, expertId):
        sql = "select p.PATENT_ID, p.name, p.abstract, p.application_no, p.inventors, p.applicant, p.year from expert_patent_join j JOIN patent p on j.PATENT_ID=p.PATENT_ID where j.EXPERT_ID='" + expertId + "';"
        cur = self.getConnection().cursor()
        cur.execute(sql)
        r = cur.fetchall()
        result = []
        for line in r:
            if line[2] is None:
                abstract = ''
            else:
                abstract = line[2]
            result.append([line[0], line[1], abstract, None, line[3], line[4], line[5], line[6]])
        return result

    # 返回一个作者的项目，包括非第一作者
    def getProjects(self, expertId):
        sql = "select p.PROJECT_ID, p.name, p.abstract_ch, p.member, p.unit, p.year, p.type from expert_project_join j JOIN project p on j.PROJECT_ID=p.PROJECT_ID where j.EXPERT_ID='" + expertId + "';"
        cur = self.getConnection().cursor()
        cur.execute(sql)
        r = cur.fetchall()
        result = []
        for line in r:
            if line[2] is None:
                abstract = ''
            else:
                abstract = line[2]
            result.append([line[0], line[1], abstract, None, line[3], line[4], line[5], line[6]])
        return result

    def __del__(self):
        self.conn.close()
