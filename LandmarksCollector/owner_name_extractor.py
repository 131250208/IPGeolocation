import json
from bs4 import BeautifulSoup
import re
from Tools import purifier
import requests
from LandmarksCollector import settings
from Tools import requests_tools as rt
from Tools.mylogger import Logger
from Tools import ocr_tool, ner_tool
logger = Logger("../Log/owner_identification_us.log")


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


def extract_copyright_info(soup):
    # copyright extracting
    list_copyright_info = []
    # pattern = "((((c|C)opyright)?\s?(&copy;|©|\(c\)|（c）)\s?((c|C)opyright)?)|(&copy;|©))"
    pattern = "(((c|C)opyright)|(&copy;|©|\(c\)|（c）))"
    list_copyright_tag = soup.find_all(text=re.compile(pattern))
    if len(list_copyright_tag) > 0:
        cpy = list_copyright_tag[-1]  # deeper, more specific
        p = cpy.parent
        copyright_text = p.text
        copyright_text = purifier.prettify_text(copyright_text)
        list_copyright_info.append(copyright_text)

    return list_copyright_info


def extract_logo(soup, url=None):
    # logo extracting
    list_image = soup.select("img")
    list_logo = []
    for img in list_image:
        str_tag = str(img).lower()
        for black_w in settings.BlACK_LIST_LOGO:
            if black_w in str_tag: continue

        try:
            img_src = img["src"]
        except KeyError as ke:
            continue
        img_name = img_src.split("/")[-1].split(".")[0]
        img_alt = img["alt"] if "alt" in img.attrs else ""
        img_id = img["id"] if "id" in img.attrs else ""
        img_title = img["title"] if "title" in img.attrs else ""
        img_class = " ".join(img["class"]) if "class" in img.attrs else ""

        str_indi = " ".join((img_name, img_alt, img_id, img_class, img_title))

        if "logo" in str_indi.lower():
            # link host with path of the img, pay attention to relative path and those already include scheme
            if url is not None:
                img_src = rt.recover_url(url, img_src)
            list_logo.append({"src": img_src, "alt": img_alt, "title": img_title})
    return list_logo


def extract_org_fr_logo(soup, url):
    reduntant_words = settings.COMPANY_ABBR
    compile_redundant_str = "(%s)" % "|".join(reduntant_words)

    list_logo = extract_logo(soup, url)
    list_entities_fr_logo = []
    for logo in list_logo:
        logo_name = logo["src"].split("/")[-1].split(".")[0]
        logo_name = re.sub(compile_redundant_str, "", logo_name, flags=re.I)
        logo_name = re.sub("[\\x21-\\x2f\\x3a-\\x40\\\x5b-\\x60\\x7b-\\x7e]+", " ", logo_name)  # del all characters
        logo_name = re.sub("\d", "", logo_name)

        logo_alt = re.sub(compile_redundant_str, "", logo["alt"], flags=re.I)
        logo_title = re.sub(compile_redundant_str, "", logo["title"], flags=re.I)

        logo_text = ""
        try:
            '''use baidu api to ocr imgs'''
            # img_format = logo["src"].split(".")[-1]
            # img_format = re.sub("\?.*", "", img_format)  # debug './temp.jpg?itok=w2hy4cip'
            # if img_format == "svg":
            #     continue
            # res = requests.get(logo["src"], proxies=rt.get_proxies_abroad(), timeout=30)
            # if res.status_code == 200:
            #     open("./temp.png", "wb").write(res.content)
            #
            #     #     drawing = svg2rlg("./temp.svg")
            #     #     renderPM.drawToFile(drawing, "./temp.png")
            #     #     img_format = "png"
            #     res_ocr = ocr_tool.img_orc_baidu("./temp.png")
            #     words_result = res_ocr["words_result"] if "words_result" in res_ocr else []
            #     list_logo_words = []
            #     for words in words_result:
            #         list_logo_words.append(words["words"])
            #     logo_text = " ".join(list_logo_words)
            '''use google api to ocr imgs'''
            ocr_res = ocr_tool.img_orc_google(logo["src"])
            if ocr_res is None: # access url fail, download manually
                img_format = logo["src"].split(".")[-1]
                img_format = re.sub("\?.*", "", img_format) # debug './temp.jpg?itok=w2hy4cip'
                if img_format == "svg":
                    logo_text = ""
                else:
                    res = requests.get(logo["src"], proxies=rt.get_proxies_abroad(), timeout=30)
                    if res.status_code == 200:
                        open("./temp.png", "wb").write(res.content)
                        ocr_res = ocr_tool.img_orc_google("./temp.png")
                        logo_text = purifier.prettify_text(ocr_res) if ocr_res is not None else ""
        except Exception as e:
            logger.war(e)
            continue
        list_entities_fr_logo.append({"logo_name": logo_name, "logo_alt": logo_alt, "logo_title": logo_title,
                                      "logo_text": logo_text})
    return list_entities_fr_logo


def extract_org_fr_copyright(soup):
    list_copyright_info = extract_copyright_info(soup)

    compile_redundant_str = "(%s)" % "|".join(settings.COMPANY_ABBR + settings.REDUNDANT_LIST_COPYRIGHT)

    list_entities_fr_cpy = []
    for copyright_info in list_copyright_info:
        res_ner = ner_tool.ner_stanford(copyright_info)
        pattern_cpy = "(((c|C)opyright)|(&copy;|©|\(c\)|（c）))"
        pattern_year = "(19|20)\d{2}"
        if "ORGANIZATION" in res_ner:
            for org in res_ner["ORGANIZATION"]:
                org = re.sub(compile_redundant_str, "", org, flags=re.I)
                org = re.sub(pattern_cpy, "", org)
                org = re.sub(pattern_year, "", org)
                list_entities_fr_cpy.append(org)

        if "LOCATION" in res_ner:
            for loc in res_ner["LOCATION"]:
                loc = re.sub(compile_redundant_str, "", loc, flags=re.I)
                loc = re.sub(pattern_cpy, "", loc)
                loc = re.sub(pattern_year, "", loc)
                list_entities_fr_cpy.append(loc)

    return list_entities_fr_cpy


def get_title(soup):
    title = ""
    tag_title = soup.select_one("title")
    if tag_title is not None:
        title = tag_title.text.strip()

    return title


def concatenate_entities(list_entities):
    query_str = ""
    list_entities = sorted(list_entities, key=lambda x:len(x), reverse=True)

    for entity in list_entities:
        if entity.lower() not in query_str.lower() and len(entity) >= 3:
            query_str += entity + ", "
    return query_str


def get_org_info_fr_pageinfo(html, url):
    '''
    iterator, use next() to get query
    if addrs work, don't need to ocr logo, in order to save some money for google api
    :param html:
    :param url:
    :return:
    '''

    # get organization info
    soup = purifier.get_pure_soup_fr_html(html)
    # title = get_title(soup)

    list_entities_fr_cpy = extract_org_fr_copyright(soup)

    # list_entities_fr_logo = extract_org_fr_logo(soup, url)
    # list_logo_text = [en["logo_text"] for en in list_entities_fr_logo]
    # list_logo_name= [en["logo_name"] for en in list_entities_fr_logo]
    # list_logo_alt = [en["logo_alt"] for en in list_entities_fr_logo]
    # list_logo_title = [en["logo_title"] for en in list_entities_fr_logo]

    query1 = concatenate_entities(list_entities_fr_cpy)

    # list_entities = [title, ]
    # list_entities.extend(list_entities_fr_cpy)
    # query2 = concatenate_entities(list_entities)

    # list_entities.extend(list_logo_title)
    # query3 = concatenate_entities(list_entities)
    # list_entities.extend(list_logo_text)
    # query4 = concatenate_entities(list_entities)
    # list_entities.extend(list_logo_alt)
    # query5 = concatenate_entities(list_entities)
    # list_entities.extend(list_logo_name)
    # query6 = concatenate_entities(list_entities)

    # query7 = title
    # query8 = concatenate_entities(list_logo_title)
    # query9 = concatenate_entities(list_logo_text)
    # query10 = concatenate_entities(list_logo_alt)
    # query11 = concatenate_entities(list_logo_name)

    tuple_query = (query1, ) # 654321 7891011
    list_query = []
    for q in tuple_query: # remove the redundant str
        if q.strip() not in list_query and q.strip() != "":
            list_query.append(q.strip())
    for q in list_query:
        yield q

# Copyright © 2015 - 2016 Shandong Shengwen Environmental Protection Technology Co., Ltd. All Rights Reserved.
    # Copyright (c) 2007 NTTPC Communications, Inc. All rights reserved.
    # © 2003-2011 中国民航科学技术研究院 版权所有 京ICP备05040221号
    # '海安县畜牧兽医站©2012 版权所有 苏ICP备12072250号
    # All Right Reserved. © 2015 Kyowa EXEO Corporation
    # Yenlo Managed Services and 2.4.6 Copyright 2001-2015 by Zabbix SIA
    # 智能网络监控系统Copyright © 2018 Shanghai Technology All rights Reserved.

'''
-------------------------------------------------------------------------------------------------------------
get organization name from registration databases
'''


def get_org_name_by_ripe(ip):
    api = "https://rest.db.ripe.net/search.json?source=ripe&query-string=%s" % ip # &source=apnic-grs
    res = rt.try_best_request_get(api, 999, "get_org_name_by_ripe")
    if res is None or res.status_code != 200:
        return None

    try:
        json_res = json.loads(res.text)
        list_object = json_res["objects"]["object"]
        descr = []

        for ob in list_object:
            if ob["type"] == "organisation":
                list_attr = ob["attributes"]["attribute"]
                for attr in list_attr:
                    if attr["name"] == "org-name":
                        return attr["value"]
    except Exception:
        return None


def get_org_name_by_arin(ip):
    api = "https://whois.arin.net/rest/ip/%s" % ip
    res = rt.try_best_request_get(api, 999, "get_org_name_by_arin")
    if res is None or res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, "lxml")
    handle = soup.select_one("handle").text

    api2 = "https://whois.arin.net/rest/net/%s/pft.json?s=%s" % (handle, ip)
    res = rt.try_best_request_get(api2, 5, "get_org_name_by_arin")
    if res is None or res.status_code != 200:
        return None

    name = None
    json_whois = json.loads(res.text)["ns4:pft"]

    if "org" in json_whois:
        org = json_whois["org"]
        name = org["name"]["$"]
    if "customer" in json_whois:
        customer = json_whois["customer"]
        name = customer["name"]["$"]

    return name


def get_org_name_by_lacnic(ip):
    api = "https://rdap.registro.br/ip/%s" % ip
    res = rt.try_best_request_get(api, 999, "get_org_name_by_lacnic")
    if res is None or res.status_code != 200:
        return None

    json_whois = json.loads(res.text)

    list_vcard = json_whois["entities"][0]["vcardArray"][1]
    for c in list_vcard:
        if c[0] == "fn":
            return c[3]

    return None


def get_org_name_by_apnic(ip):
    pass


def get_org_name_by_registration_db(ip):
    org = get_org_name_by_arin(ip)
    # Asia Pacific Network Information Centre, South Brisbane # http://wq.apnic.net/query?searchtext=111.204.219.195

    if org is not None and "RIPE Network Coordination Centre" in org:
        org = get_org_name_by_ripe(ip)

    if org is not None and "Latin American and Caribbean IP address Regional Registry" in org:
        org = get_org_name_by_lacnic(ip)

    if org is None:
        return None

    reduntant = ["Inc", "LLC", ".com", "L.L.C", "Ltd", "technology", "Technologies"]
    pattern = "(%s)" % "|".join(reduntant)
    org = re.sub(pattern, "", org, re.I)

    return org


if __name__ == "__main__":
    whois = get_org_name_by_registration_db("34.200.30.249")
    print(whois)
    pass









