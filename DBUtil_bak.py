#!/usr/bin/env python
# -*- coding: utf-8 -*-


from DBUtils.PooledDB import PooledDB
import MySQLdb


class DB(object):

    def __init__(self):
        print "create MySQL pool!!!!!!"
        self.pool = PooledDB(
            MySQLdb,
            10,                     # 10为连接池里的最少连接数
            host='10.1.13.29',
            user='root',
            passwd='tdlabDatabase',
            db='techpooldata',
            port=3306
        )
        self.tables = {'paper': 'expert_paper_join', 'patent': 'expert_patent_join', 'project': 'expert_project_join'}
        self.columns = {'paper': 'PAPER_ID', 'patent': 'PATENT_ID', 'project': 'PROJECT_ID'}

    # 返回以docId为key，以authors为value的map
    def getAuthors(self, typee, ids):
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
        conn = self.pool.connection()
        cur = conn.cursor()
        cur.execute(sql)
        results = cur.fetchall()
        cur.close()
        conn.close()
        for line in results:
            if line[0] not in authorIds:
                authorIds[line[0]] = []
            authorIds[line[0]].append(line[1])
        return authorIds

    # 返回id是否在数据库中，因为有时数据不同步
    def idInDB(self, typee, id):
        conn = self.pool.connection()
        cur = conn.cursor()
        sql = "select * from " + self.tables[typee] + " where " + self.columns[typee] + " ='" + id + "'"
        count = cur.execute(sql)
        cur.close()
        conn.close()
        return count > 0

    # 返回一个作者的论文，包括非第一作者
    def getPapers(self, expertId):
        sql = "select p.PAPER_ID, p.name, p.abstract,p.authors, p.journal_name, p.year from expert_paper_join j JOIN paper p on j.PAPER_ID=p.PAPER_ID where j.EXPERT_ID='" + expertId + "';"
        conn = self.pool.connection()
        cur = conn.cursor()
        cur.execute(sql)
        r = cur.fetchall()
        result = []
        for line in r:
            if line[2] is None:
                abstract = ''
            else:
                abstract = line[2]
            result.append([line[0], line[1], abstract, None, line[3], line[4], line[5]])
        cur.close()
        conn.close()
        return result

    # 返回一个作者的专利，包括非第一作者
    def getPatents(self, expertId):
        sql = "select p.PATENT_ID, p.name, p.abstract, p.application_no, p.inventors, p.applicant, p.year from expert_patent_join j JOIN patent p on j.PATENT_ID=p.PATENT_ID where j.EXPERT_ID='" + expertId + "';"
        conn = self.pool.connection()
        cur = conn.cursor()
        cur.execute(sql)
        r = cur.fetchall()
        result = []
        for line in r:
            if line[2] is None:
                abstract = ''
            else:
                abstract = line[2]
            result.append([line[0], line[1], abstract, None, line[3], line[4], line[5], line[6]])
        cur.close()
        conn.close()
        return result

    # 返回一个作者的项目，包括非第一作者
    def getProjects(self, expertId):
        sql = "select p.PROJECT_ID, p.name, p.abstract_ch, p.member, p.unit, p.year, p.type from expert_project_join j JOIN project p on j.PROJECT_ID=p.PROJECT_ID where j.EXPERT_ID='" + expertId + "';"
        conn = self.pool.connection()
        cur = conn.cursor()
        cur.execute(sql)
        r = cur.fetchall()
        result = []
        for line in r:
            if line[2] is None:
                abstract = ''
            else:
                abstract = line[2]
            result.append([line[0], line[1], abstract, None, line[3], line[4], line[5], line[6]])
        cur.close()
        conn.close()
        return result
