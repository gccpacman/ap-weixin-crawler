#!/usr/bin/python
# encoding=utf8


import re
import json
import requests
import time
import sys

LOGFILE = '/var/log/squid3/access.log'
TABLE = 'wx_post_simple'


class PatchSimple(object):
    def __init__(self, url):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 MicroMessenger/4.5.255'}
        self.p_url = url['p_url']
        self.url_hash = url['url_hash']
        self.gzh_id = url['gzh_id']
        self.id = url['id']

    def parse_key_from_squid(self):
        lines = open(LOGFILE).readlines()
        lines.reverse()
        p = re.compile(r'__biz=([^&]+).*?uin=([^& ]+).*?key=([^& ]+)')
        for l in lines:
            m = p.findall(l)
            if not m:
                continue
            self.biz = m[0][0]
            self.uin = m[0][1]
            self.key = m[0][2]
            # print '\rparse_key_from_squid:', m[0],
            sys.stdout.flush()
            break

    @staticmethod
    def get_p_date(content):
        p_date = re.search(r'media_meta_text">(.*?)<', content).groups()[0]
        # year, month, day = re.search(r'media_meta_text">(\d*?)-(\d*?)-(\d*?)<', r.content'").groups()
        return p_date

    def get_p_author(self, content):
        author = re.search(r'rich_media_meta_nickname">(.*?)<\/sp', content).groups()[0]
        self.author = author

    def get_read_like_num(self):
        # if self.url_has_like_num():
        #     print 'has like num',
        #     return
        post_url = ''
        pre_post_url = ''
        pre_post_url = self.p_url.replace('#wechat_redirect', '')
        pre_post_url = pre_post_url.replace('mp.weixin.qq.com/s', 'mp.weixin.qq.com/mp/getappmsgext')
        # pre_post_url = self.num_url.replace('mp.weixin.qq.com/s', 'mp.weixin.qq.com/mp/getappmsgext')
        post_url = pre_post_url + '&f=json&uin=%s&key=%s' % (self.uin, self.key)
        # print "[*] Post_url", post_url
        # gzh_name = self.get_gzh_name(self.gzh_id)
        gzh_name = '-test'
        print "[*] gzh_name:", gzh_name, self.id
        r = requests.post(post_url, headers=self.headers)
        time.sleep(2)
        if 'appmsgstat' not in r.content:
            time.sleep(10)
            self.wait_for_new_keys()
            print '-' * 10
            self.get_read_like_num()
            print '-' * 10
            return
        j = json.loads(r.content)
        self.read_num = j[u'appmsgstat'][u'read_num']
        self.like_num = j[u'appmsgstat'][u'like_num']
        # self.update_db()

    def wait_for_new_keys(self):
        print "[**] The key is invalied,and not find new key, sleep per 5s."
        i = 0
        while 1:
            self.parse_key_from_squid()
            # print "ori_key:", self.ori_key
            # print "now_key:", self.key
            if self.key != self.ori_key:
                self.ori_key = self.key
                print "[*] Get new key, continue work!"
                return
            else:
                print "\rwait new key %s" % ('.'*i),
                sys.stdout.flush()
                time.sleep(10)
                i += 1

    def mk_url(self):
        print self.p_url
        self.parse_key_from_squid()
        self.update_key()
        pre_url_2 = '&uin=%s&key=%s'
        pre_url = self.p_url.replace('#wechat_redirect', '')
        self.num_url = pre_url + pre_url_2 % (self.uin, self.key)

    def update_key(self):
        self.ori_key = self.key

    def get_author_and_date(self):
        r = requests.get(self.num_url)
        time.sleep(1)
        open('content.html', 'w').write(r.content)
        try:
            self.date = self.get_p_date(r.content)
            self.get_p_author(r.content)
        except Exception, e:
            if '该内容已被发布者删除' in r.content:
                self.date = ''
                self.author = ''
            else:
                print Exception, e

    def start(self):
        self.mk_url()
        # print "[*] num_url:", self.num_url
        # self.get_author_and_date()
        self.get_read_like_num()

def go():
    ps = PatchSimple(url)
    ps.start()


if __name__ == '__main__':
    go()
