#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bottle
import json
import logging
import logging.config
import utils

#logging.config.fileConfig('logger.conf')
#logger = logging.getLogger('recommServerLog')
#logger.info('系统启动...')

#import similarity

#recmder = similarity.Recommander('./data/wm.bin','./data/ind/paper.ind','./data/ind/patent.ind','./data/ind/project.ind')

@bottle.route('/recommend/test.do')
def get_similar_project():
    n = int(bottle.request.query['topN'])
    txt = bottle.request.query.words
    print txt
    bottle.response.content_type = 'text/html; charset=utf-8'
    return json.dumps(dict(l))

@bottle.route('/recommend/paper.do')
def get_similar_paper():
    n = int(bottle.request.query['topN'])
    txt = bottle.request.query.words

    logger.info(u'#####收到请求，参数：%s,%s' % (n,txt))
    bottle.response.content_type = 'text/html; charset=utf-8'
    l = [('7a753384-b861-11e6-af90-005056b3f30e',0.12),('38479004-b88c-11e6-af90-005056b3f30e',0.93)]
    return json.dumps(dict(l))

@bottle.route('/recommend/patent.do')
def get_similar_patent():
    n = int(bottle.request.query['topN'])
    txt = bottle.request.query.words
    bottle.response.content_type = 'text/html; charset=utf-8'
    l = [('3738fe07-b7a7-11e6-af90-005056b3f30e',0.12),('3739085d-b7a7-11e6-af90-005056b3f30e',0.93)]
    return json.dumps(dict(l))

@bottle.route('/recommend/project.do')
def get_similar_project():
    n = int(bottle.request.query['topN'])
    txt = bottle.request.query.words
    bottle.response.content_type = 'text/html; charset=utf-8'
    l = [('227948d3-b19a-11e6-8836-005056b3f30e',0.123787622),('fa4d2d6d-b199-11e6-8836-005056b3f30e',0.93)]
    return utils.l2m_str(l)

@bottle.route('/analysis/is_contain.do')
def is_contain():
    w = bottle.request.query.w
    return json.dumps(False)

if __name__ == '__main__':
    bottle.run(host='0.0.0.0',port=8080)
