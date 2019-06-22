#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket


def l2m_str(l):
    return '{%s}' % ','.join(['"%s":' % a + str(b) for a, b in l])


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip
