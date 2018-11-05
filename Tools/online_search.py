from bs4 import BeautifulSoup
import requests
from urllib import parse
import random
import json
import sys
import time
import re
from Tools import purifier, geolocation
import logging
from Tools import requests_tools as rt, settings

def random_sleep():
    random.seed(time.time())
    sleeptime = random.random() * 3
    time.sleep(sleeptime)


def quote(queryStr):
    try:
        queryStr = parse.quote(queryStr)
    except:
        queryStr = parse.quote(queryStr.encode('utf-8', 'ignore'))

    return queryStr


#  url = 'https://www.bing.com/search?q=%s&setmkt=en-us&setlang=en-us' % queryStr
def google_search(queryStr):
    queryStr = quote(queryStr)
    url = 'https://www.google.com/search?q=%s' % queryStr

    response = rt.try_best_request_get(url, 5, "google_search", "abroad")
    html = response.text
    return html


def extract_search_results(html):
    soup = BeautifulSoup(html, "lxml")
    results = []
    div = soup.find('div', id='search')
    if div:
        lis = div.findAll('div', {'class': 'g'})
        if len(lis) > 0:
            for li in lis:
                out = {}
                h3 = li.find('h3', {'class': 'r'})
                if h3 is None:
                    continue
                out["name"] = h3.getText()
                if h3 is None:
                    continue

                link = h3.find('a')
                if link is None:
                  continue 
                out["url"] = link['href']

                span = li.find('span', {'class': 'st'})
                if span is  not None:
                    content = span.getText()
                    out["snippet"] = content

                results.append(out)
    return results


def google_search_format(t_keywords):
    while True:
        try:
            html = google_search(t_keywords)
            soup = BeautifulSoup(html, "lxml")
            kg_panel = soup.select_one("div.knowledge-panel")
            if kg_panel is None:
                print("kgp is none")
                continue
            parents_website = kg_panel.find(text="Website").parents
            for p in parents_website:
                if p.name == "a":
                    website = p["href"]
                    break
        except AssertionError:
            continue
    return website


def google_kg_search(query_str):
    api = "https://kgsearch.googleapis.com/v1/entities:search?query=%s&key=%s&limit=1&indent=True" % (quote(query_str), settings.GOOGLE_API_KEY)
    res = rt.try_best_request_get(api, 5, "google_kg_search", "abroad")
    if res is None or res.status_code != 200:
        return ""
    return res.text


def ripe_db_search(ip):
    api = "https://rest.db.ripe.net/search.json?source=ripe&query-string=%s" % ip # &source=apnic-grs
    res = rt.try_best_request_get(api, 5, "ripe_db_search")
    if res is None or res.status_code != 200:
        return ""

    try:
        json_res = json.loads(res.text)
        list_object = json_res["objects"]["object"]
        descr = []

        for ob in list_object:
            if ob["type"] == "inetnum":
                list_attr = ob["attributes"]["attribute"]
                for attr in list_attr:
                    if attr["name"] == "descr":
                        descr.append(attr["value"])
    except Exception:
        return ""

    return ",".join(descr)


def arin_whois_rws_search(ip):
    api = "https://whois.arin.net/rest/ip/%s" % ip
    res = rt.try_best_request_get(api, 5, "arin_whois_rws_search", "abroad")
    if res is None or res.status_code != 200:
        return ""

    soup = BeautifulSoup(res.text, "lxml")
    handle = soup.select_one("handle").text

    api2 = "https://whois.arin.net/rest/net/%s/pft.json?s=%s" % (handle, ip)
    res = rt.try_best_request_get(api2, 5, "arin_whois_rws_search", "abroad")
    if res is None or res.status_code != 200:
        return ""

    # soup = BeautifulSoup(res.text, "lxml")
    #
    # city = soup.select_one("org > city")
    # if city is None:
    #     city = soup.select_one("customer > city")
    #
    # name = soup.select_one("org > name")
    # if name is None:
    #     name = soup.select_one("customer > name")

    # try:
    #     whois_info = name.text + ", " + city.text
    # except:
    #     pass
    city = ""
    name = ""
    json_whois = json.loads(res.text)["ns4:pft"]
    if "org" in json_whois:
        org = json_whois["org"]
        city = org["city"]["$"]
        name = org["name"]["$"]
    if "customer" in json_whois:
        customer = json_whois["customer"]
        city = customer["city"]["$"]
        name = customer["name"]["$"]

    return name + ", " + city


def get_orginfo_by_whois_rws(ip):
    arin = arin_whois_rws_search(ip)
    # Latin American and Caribbean IP address Regional Registry, Montevideo # https://rdap.registro.br/ip/201.54.140.10
    # Asia Pacific Network Information Centre, South Brisbane # http://wq.apnic.net/query?searchtext=111.204.219.195
    #
    if "RIPE Network Coordination Centre" in arin:
        return ripe_db_search(ip)

    reduntant = ["Inc.", "LLC", ".com"]
    pattern = "(%s)" % "|".join(reduntant)
    arin = re.sub(pattern, "", arin, re.I)
    return arin


# District of Columbia,
if __name__ == '__main__':
    # print(google_web_search("suXus X-central Remote Monitoring & Management Solution"))

    # res = geolocation.google_map_places_search("VPISU")
    # print(res)

    whois = arin_whois_rws_search("138.123.240.163")
    print(whois)
    # ripe = ripe_db_search("129.16.71.10")
    # coord = geolocation.google_map_coordinate(whois)
    # geolocation.dis_btw_2p(whois, "Delaware College of Art and Design US")
    # # print(ripe)
    # print(coord)
    # res_ipip = geolocation.ip_geolocation_ipip("34.215.139.216")
    # print(res_ipip)

    # import pyprind
    # sch_us = json.load(open("../resources/school_us_0.2.json", "r"))
    # count_fail = 0
    # for sch in pyprind.prog_bar(sch_us):
    #     if "url" not in sch:
    #         count_fail += 1
    # print(len(sch_us) - count_fail)

    # for sch in pyprind.prog_bar(sch_us):
    #     state_name = sch["state_name"]
    #     school_name = sch["school_name"]
    #     item_res = google_kg_search(school_name)
    #     try:
    #         json_item = json.loads(item_res)
    #         website = json_item["itemListElement"][0]["result"]["url"]
    #         sch["url"] = website
    #     except Exception:
    #         continue
    #     print(sch)
    #
    # json.dump(sch_us, open("../resources/school_us_0.2.json", "w"))



