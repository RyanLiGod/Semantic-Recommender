#!/usr/bin/env python
#-*- coding:utf-8 -*-

import json
import similarity
import codecs
import MySQLdb as DB

#调节索引平面分割为50的时候，测试最近N的效果，有索引计算出来只能得到论文，专利，人，项目的ID号，需要连接数据库进行查询，并将查询的结果保存到本地

#连接服务器中的数据库
con = DB.connect('10.1.13.29','root','tdlabDatabase','techpooldata',charset='utf8')
cur = con.cursor()
recmder = similarity.Recommander('/testdata/data/wm.bin','/testdata/data/ind/paper.ind','/testdata/data/ind/patent.ind','/testdata/data/ind/project.ind')

change_simi_output = codecs.open(r'/testdata/data/test/testindex50Result.txt','w', 'utf-8')

with codecs.open(r'/testdata/data/test/testKeyword.txt', 'r', 'utf-8') as text:
    for each_text in text:
	each_text = each_text.strip('\n')
	change_simi_output.write(each_text + '\n')		
	top10_simiPaper = recmder.most_similar_paper(u'%s' % each_text)
	#top10_simiPatent = recmder.most_similar_patent(u'%s' % each_text)			
	#top10_simiProject = recmder.most_similar_project(u'%s' % each_text)
	#for paperID, patentID, projectID in top10_simiPaper, top10_simiPatent, top10_simiProject:
	for paperID in top10_simiPaper:

	    selePaper = "SELECT name, abstract FROM paper WHERE PAPER_ID='%s'" % paperID[0]
	    cur.execute(selePaper)
	    results = cur.fetchall()
	    for words in results:	
            	change_simi_output.write('  '+ str(paperID[1]) +'  '+ words[0] +'\n')
		change_simi_output.write('      '+ words[1] +'\n')






