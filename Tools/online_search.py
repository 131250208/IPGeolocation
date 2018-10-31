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
    return res.text

# District of Columbia,
if __name__ == '__main__':
    # print(google_web_search("suXus X-central Remote Monitoring & Management Solution"))
    # whois("143.248.48.110")
    print(google_kg_search("Wyoming Technical Institute (WyoTech)"))

