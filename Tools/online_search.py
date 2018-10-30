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
from Tools import requests_tools as rt

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

    try:
        response = requests.get(url, headers=rt.headers, proxies=rt.get_proxies_abroad(), timeout=10)
        html = response.text
    except:
        print("connection error")
        return ""
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
    html = google_search(t_keywords)
    res = extract_search_results(html)
    if len(res) == 0:
        sys.stderr.write("..... search again ...")
        random_sleep()
        html = google_search(t_keywords)
        res = extract_search_results(html)
        return res
    return res

# District of Columbia,
if __name__ == '__main__':
    # print(google_web_search("suXus X-central Remote Monitoring & Management Solution"))
    # whois("143.248.48.110")
    print(geolocation.google_map_coordinate("徐州"))

