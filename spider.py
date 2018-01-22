#!/usr/bin/env python3
#coding=utf-8
import requests
import sqlite3
import time
import sys
from html.parser import HTMLParser
from lxml import etree
import colorama

ex_log = False
base_url = "http://www.kguowai.com"

def log_out(content, *args):
    print(time.strftime('\033[32m[%Y-%m-%d %H:%M:%S]\033[0m ', time.localtime(time.time())) + content, *args)
    sys.stdout.flush()
    if ex_log:
        f_log = open("spider.log", "a")
        print(time.strftime('[%Y-%m-%d %H:%M:%S] ', \
            time.localtime(time.time())) + content, *args ,file = f_log)
        f_log.close()
    return


# init db
def init_db():
    global conn
    conn = sqlite3.connect("webdata.db")
    log_out("DB link success.")
    c = conn.cursor()
    data = c.execute('SELECT name FROM sqlite_master;')
    for row in data:
        if (row[0]!='sqlite_sequence'):
            c.execute('DROP TABLE %s;' %row[0])
    c.execute('DELETE FROM sqlite_sequence;')
    c.execute('''
        CREATE TABLE sites (
            id          INTEGER NOT NULL    PRIMARY KEY AUTOINCREMENT   UNIQUE,
            name        TEXT    NOT NULL,
            url         TEXT,
            country     TEXT,
            category    TEXT,
            description TEXT
        );
    ''')
    conn.commit()

def write_db(name, url, country, category, description):
    conn.cursor().execute('INSERT INTO sites (name, url, country, category, description)\
        VALUES (?, ?, ?, ?, ?)', (name, url, country, category, description))
    conn.commit()


if __name__ == "__main__":
    colorama.init()
    init_db()
    nextpage = True
    pagenumber = 0
    # walk pages
    while(nextpage):
        pagenumber += 1
        url = "http://www.kguowai.com/all/index"
        if (pagenumber > 1) : url += ("_%d.html" %pagenumber)
        else : url += ".html"
        log_out("Getting page %s" %url)
        r = requests.get(url)
        r.encoding = 'gb2312'
        html = r.text
        selector = etree.HTML(html)
        hrefs = selector.xpath('//div[@id="list_main"]/div/div/h2/a/@href')
        for index, href in enumerate(hrefs):
            log_out("Processing link %d in page %d" % (index, pagenumber))
            log_out(href)
            r = requests.get(href)
            r.encoding = 'gb2312'
            html = r.text
            selector = etree.HTML(html)
            name = selector.xpath('//strong[text()="名称"]/../h1/text()')[0]
            url_s = selector.xpath('//strong[text()="网址"]/../a[1]/@href')
            if len(url_s) == 0 :
                url_s = selector.xpath('//strong[text()="外文网址"]/../a[1]/@href')
            if len(url_s) != 0: url = url_s[0]
            else : url=""
            country = selector.xpath('//div[@id="position"]/a[3]/text()')[0]
            category = selector.xpath('//div[@id="position"]/text()')[3][3:]
            cate_end = category.find('>')
            category = category[:cate_end - 1]
            description_s = selector.xpath('//div[@id="sitetext"]/text()')
            description = ""
            for description_m in description_s:
                description += description_m
            write_db(name, url, country, category, description)


        nextpage = (len(selector.xpath('//li[@class="next"]/a/text()'))==0)

    conn.close()
    
