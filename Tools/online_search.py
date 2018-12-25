from bs4 import BeautifulSoup
import requests
from urllib import parse
import random
import json
import sys
import time
import re
from Tools import purifier, geo_distance_calculator
import logging
from Tools import requests_tools as rt
import settings


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


def bing_search(query):
    query = quote(query)
    url = 'https://www.bing.com/search?q=%s&ensearch=1&FORM=QBLHCN' % query
    res = rt.try_best_request_get(url, 5)
    # soup = BeautifulSoup(res.text, "lxml")
    open("../Sources/temphtml.html", "w", encoding="utf-8").write(res.text)
    # title = soup.select_one("h2. b_entityTitle").get_text()
    # subtitle = soup.select_one("div.b_entitySubTitle").get_text()
    # snippet = soup.select_one("div.b_snippet").get_text()
    # print("{} {}\n{}".format(title, subtitle, snippet))


#  url = 'https://www.bing.com/search?q=%s&setmkt=en-us&setlang=en-us' % queryStr
def google_search(queryStr, proxy_type="None"):
    queryStr = quote(queryStr)
    url = 'https://www.google.com/search?biw=1920&safe=active&hl=en&q=%s&oq=%s' % (queryStr, queryStr)

    response = rt.try_best_request_get(url, 99, "google_search", proxy_type=proxy_type)
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


def google_kg_search(query_str):
    api = "https://kgsearch.googleapis.com/v1/entities:search?query=%s&key=%s&limit=1&indent=True" % (quote(query_str), "AIzaSyBuvFKna_9YqhszzmGNV1MIFjGNnfz8uyk")
    res = rt.try_best_request_get(api, 5, "google_kg_search", "abroad")
    if res is None or res.status_code != 200:
        return ""
    return res.text


if __name__ == '__main__':
    print(google_kg_search("Beijing"))
    pass