import gevent.monkey
import multiprocessing

gevent.monkey.patch_all()

bind = '0.0.0.0:8080'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
timeout = 100000

x_forwarded_for_header = 'X-FORWARDED-FOR'
