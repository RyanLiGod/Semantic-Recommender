#!/usr/bin/env python
# -*- coding: utf-8 -*-

def l2m_str(l):
    return '{%s}' % ','.join(['"%s":'%a + str(b) for a,b in l])

if __name__ == '__main__':
    l = [('227948d3-b19a-11e6-8836-005056b3f30e',0.123787622),('fa4d2d6d-b199-11e6-8836-005056b3f30e',0.93)]
    print l2m_str(l)
