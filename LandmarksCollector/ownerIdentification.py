import json
from bs4 import BeautifulSoup
import logging
import re
from Tools import online_search, purifier
import ner
import base64
from urllib import parse
import requests
import time
import random
import os
from LandmarksCollector.SampleReader import get_brief_one
from Tools import requests_tools as rt
from Tools.mylogger import Logger
logger = Logger("./owner_identification_us.log")
import gevent

def tokenize(text):
    '''
    tokenize img tag
    :param text:
    :return:
    '''
    text = re.sub("([A-Z]+)", r"_\1", text)
    text = text.lower()
    pattern = re.compile("[a-z\-_]+")# jdkf_df, dsf-gfg, sdf
    return pattern.findall(text)


def img_OCR(filePath):
    '''
    Baidu OCR API
    :param filePath:
    :return: text in the image
    '''
    img = open(filePath, "rb")
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token=24.41d0976869d7ae95714d188117a8b17c.2592000.1542006180.282335-14421471"
    img_bs64 = base64.b64encode(img.read()).decode()
    data = {
        "language_type": "CHN_ENG",
        "detect_direction": "true",
        "probability": "true",
        "image": img_bs64
    }
    data = parse.urlencode(data)
    res = requests.post(url, data=data)
    print(res.text)
    return json.loads(res.text)

tagger = ner.SocketNER(host='localhost', port=8080)


def ner_copyright(copyright_info):
    result = tagger.get_entities(copyright_info)
    return result

def extract_owner_entities(title, list_logo, list_copyright_info):
    list_entities_fr_title = []
    list_entities_fr_title.append(title)

    list_entities_fr_cpy = []
    for copyright_info in list_copyright_info:
        res_ner = ner_copyright(copyright_info)
        if "ORGANIZATION" in res_ner:
            list_entities_fr_cpy.extend(res_ner["ORGANIZATION"])

    list_entities_fr_logo = []
    for logo in list_logo:
        if logo["alt"] != "":
            list_entities_fr_logo.append(logo["alt"])

        try:
            res = requests.get(logo["src"], proxies=rt.get_proxies_abroad(), timeout=30)
            if res.status_code == 200:
                open("./temp.png", "wb").write(res.content)
                res_ocr = img_OCR("./temp.png")
                words_result = res_ocr["words_result"]

                for words in words_result:
                    list_entities_fr_logo.append(words["words"])
        except Exception as e:
            logger.war(e)
            continue

    return list_entities_fr_title, list_entities_fr_logo, list_entities_fr_cpy

def extract_owner_indicators(html, host, url):
    '''
    :param html:
    :param host: host of this page
    :param url: url of this page
    :return: title, list_logo, list_copyright_info
    '''
    html = purifier.get_pure_body_fr_html(html)
    soup = BeautifulSoup(html, "lxml")

    # logo extracting
    list_image = soup.select("img")
    list_logo = []
    for img in list_image:
        if "logo" in str(img).lower():
            img_src = img["src"]
            img_alt = ""
            if "alt" in img.attrs:
                img_alt = img["alt"]

            # link host with path of the img, pay attention to relative path
            pattern_backup = re.compile("\.\./")
            count_backup = len(pattern_backup.findall(img_src))
            if count_backup > 0:
                components_host = url.split("/")
                path_img = re.sub("\.\./", "", img_src)
                img_src = "/".join(components_host[:-(count_backup + 1)]) + "/" + path_img
            else:
                if img_src[0] != "/":
                    img_src = "/" + img_src
                img_src = host + img_src
            list_logo.append({"src": img_src, "alt": img_alt})

    title = ""
    tag_title = soup.select_one("title")
    if tag_title is not None:
        title = tag_title.text.strip()

    # copyright extracting
    list_copyright_info = []
    pattern = ".*?((((c|C)opyright)?\s?(&copy;|©|\(c\)|（c）)\s?((c|C)opyright)?)|(&copy;|©)).*"
    list_copyright_tag = soup.find_all(text=re.compile(pattern))
    if len(list_copyright_tag) > 0:
        for cpy in list_copyright_tag:
            for parent in cpy.parents:
                if parent.name == "div":
                    copyright_info = re.sub("[\n\r\t\s ]+", " ", parent.text)
                    list_copyright_info.append(copyright_info)
                    break

    return title, list_logo, list_copyright_info


def owner_extract(filepath):
    file_inp = open(filepath, "r", encoding="utf-8")
    ind = 0
    for line in file_inp:
        page_info = get_brief_one(line)
        if page_info is None:
            continue
        host = page_info["host"]
        url = page_info["url"]
        html = page_info["html"]
        ip = page_info["ip"]

        title, list_logo, list_cpy = extract_owner_indicators(html, host, url)
        list_ent_fr_title, list_ent_fr_logo, list_ent_fr_cpy = extract_owner_entities(title, list_logo, list_cpy)
        # if len(logo_list) == 0 and len(copyright_list) == 0:
        #     count_no_indicator += 1
        # print("ind: %d, title: %s, logo_list: %s, copyright_list: %s" % (ind, title, logo_list, copyright_list ))
        logger.debug("ind: %d, ip: %s, country: %s, title: %s, logo: %s, copyright: %s" % (ind, ip, online_search.whois(ip)[0], list_ent_fr_title, list_ent_fr_logo, list_ent_fr_cpy))
        ind += 1


def check_ping(hostname):
    response = os.system("ping " + hostname)
    # and then check the response...
    if response == 0:
        pingstatus = "Network Active"
    else:
        pingstatus = "Network Error"

    return pingstatus


def check_connection(url):
    try:
        res = requests.get(url, headers=rt.get_random_headers(), proxies=rt.get_proxies_abroad(), timeout=10)
        if res.status_code != 200:
            return False
    except Exception as e:
        # logger.war("url: %s connecting fail.." % url)
        return False
    return True


def check_line(line, country):
    page_info = get_brief_one(line)
    if page_info is None:
        return None

    ip = page_info["ip"]
    url = page_info["url"]

    # if check_connection(url) is False:
    #     return None

    line_res = None
    ip_info = online_search.whois(ip)
    if ip_info[0] == country:
        json_page_info = json.loads(line)
        json_page_info["ip_info"] = ip_info
        line_res = json.dumps(json_page_info)
    return line_res


def filter_by_country(country, path_inp, path_out, index, packet_size=100,):
    file_inp = open(path_inp, "r", encoding="utf-8")
    file_out = open(path_out, "a", encoding="utf-8")

    ind = 0
    count_temp = 0
    count_saved = 0
    ind_last = 0

    line_packet = []
    for line in file_inp:
        if ind < index:
            ind += 1
            continue

        line_packet.append(line)
        count_temp += 1
        if count_temp == packet_size:
            jobs = [gevent.spawn(check_line, line, country) for line in line_packet]
            gevent.joinall(jobs, timeout=10)
            for job in jobs:
                if job.value is not None:
                    file_out.write("%s\n" % job.value)

            file_out.close()
            file_out = file_out = open(path_out, "a", encoding="utf-8")
            ind_last = ind
            count_saved += 1
            count_temp = 0
            logger.war("--------ind: %d, count_temp: %d, count_saved: %d, last_ind: %d-----------" % (ind, count_temp, count_saved, ind_last))
        ind += 1

    file_out.close()

# Copyright © 2015 - 2016 Shandong Shengwen Environmental Protection Technology Co., Ltd. All Rights Reserved.
    # Copyright (c) 2007 NTTPC Communications, Inc. All rights reserved.
    # © 2003-2011 中国民航科学技术研究院 版权所有 京ICP备05040221号
    # '海安县畜牧兽医站©2012 版权所有 苏ICP备12072250号
    # All Right Reserved. © 2015 Kyowa EXEO Corporation
    # Yenlo Managed Services and 2.4.6 Copyright 2001-2015 by Zabbix SIA
    # 智能网络监控系统Copyright © 2018 Shanghai Technology All rights Reserved.
if __name__ == "__main__":
    # img_OCR("../sources/kaist-logo.png")
    # res = ner_copyright("Yenlo Managed Services and 2.4.6 Copyright 2001-2015 by Zabbix SIA")
    # print(res)
    # owner_extract("E:\\samples_usa.json")

    filter_by_country("United States", "E:\\samples_usa.json", "E:\\samples_us_temp.json", 0)# 575 # 372212

    # import nltk
    # text = "Copyright (c) 2007 NTTPC Communications, Inc. All rights reserved."
    # tokens = nltk.word_tokenize(text)  # 分词
    # tagged = nltk.pos_tag(tokens)  # 词性标注
    # entities = nltk.chunk.ne_chunk(tagged)  # 命名实体识别
    # for entity in entities:
    #     print(entity)








