#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
连接Redis数据库，最快的获取的方式，在失效的时候改成MySQL。
'''

import redis
import logging.config
import utils

logging.config.fileConfig('logger.conf')
logger = logging.getLogger('recommServerLog')


class RedisUtil(object):

    def __init__(self):
        if utils.get_host_ip() == '10.1.13.49':
            self.HOST = '10.1.18.26'
        else:
            self.HOST = '202.107.204.66'
        self.pool = redis.ConnectionPool(host=self.HOST, port=7070, password='123456aa', db=0)

    def get_connection(self):
        return redis.Redis(connection_pool=self.pool)

    def get_hash_key(self, name, key):
        r = self.get_connection()
        return r.hget(name, key)

    def get_hash_all(self, name):
        r = self.get_connection()
        return r.hgetall(name)

    # 返回以docId为key，以authors为value的map
    def getAuthors(self, ids):
        if len(ids) == 0:
            return {}
        authorIds = {}
        for id in ids:
            expert_info = self.get_hash_all(id)
            if expert_info == {}:
                continue
            expert_id_list = []
            for expert_role in expert_info.keys():
                expert_id_list.append(expert_info[expert_role])
            authorIds[id] = expert_id_list
        return authorIds
