import logging
from bs4 import BeautifulSoup
import json
import re
from LandmarksCollector import settings
from Tools import geolocation as geo


def is_valid(line):
    '''
    check:
        not "\n",
        can be loaded by json,
        not error page,
        has status_code and it is 200

    :param line: a line of bytes read from file
    :return: boolen
    '''

    line = line.decode("utf-8")

    if line.strip("\n") == "":
        return False

    # filter json loading fail
    try:
        banner_info = json.loads(line)
    except Exception as e:
        logging.warning(e)
        logging.warning("error str can not be loads as json: %s" % line)
        return False

    if "error" in banner_info:  # filter error pages
        return False

    # filter samples without status code
    try:
        status_code = banner_info["data"]["http"]["response"]["status_code"]
    except Exception as e:
        logging.warning(e)
        logging.warning("has no status_code: %s" % line)
        return False

    if status_code != 200:  # filter pages of which status code is not 200
        return False
    return True


def get_brief_one(line):
    '''
    get brief info from line, including:
        "title": title,
        "url": "%s://%s%s" % (scheme, host, path),
        "html": html,
        "ip": ip,
        "host": "%s://%s" % (scheme, host),
    :param line:
    :return:
            None:
                can not be loaded by json
                if no url(scheme, host, path) in sample

            Else:
                a dict including "title", "url", "html", "ip", "host"
            FYI, sometimes title can be "".
    '''
    try:
        banner_info = json.loads(line.decode("utf-8"))
    except Exception as e:
        logging.warning(e)
        return None

    ip = banner_info["ip"]
    response = banner_info["data"]["http"]["response"]
    if "body" in response:
        html = response["body"]
    else:
        return None

    if html.strip() == "":
        return None

    title = ""
    soup = BeautifulSoup(html, "lxml")
    tag_title = soup.select_one("title")
    if tag_title is not None:
        title = tag_title.get_text()
    else:
        match = re.search("<title[^>]*>(.*)</title>", html)
        if match is not None:
            title = match.group(1)

    try:
        url = response["request"]["url"]
        scheme = ""
        host = ""
        path = ""
        if "scheme" in url:
            scheme = url["scheme"]
        if "host" in url:
            host = url["host"]
        if "path" in url:
            path = url["path"]

        return {"title": title,
                "url": "%s://%s%s" % (scheme, host, path),
                "html": html,
                "ip": ip,
                "scheme": scheme,
                "host": host,
                "path": path,
                }
    except Exception as e:
        logging.warning(e)
        return None


def check_title(title):
    for w in settings.BlACK_LIST_INVALID_PAGE:
        if w.lower() in title.lower():
            return False
    return True


def filter_transaction_us(infilepath, outfilepath, index):
    '''
    for data from ipv4 space ~ 700G
    :param infilepath:
    :return:
    '''
    f = open(infilepath, "rb")
    out = open(outfilepath, "a", encoding="utf-8")

    ind = 0
    count_temp = 0
    save_size = 1000
    saved_time = 0
    for line in f:
        if ind < index:
            ind += 1
            continue
        page_info = get_brief_one(line) if is_valid(line) else None
        if page_info is not None and check_title(page_info["title"]):
            ipip = geo.ip_geolocation_ipip(page_info["ip"])
            if ipip["country"] == "United States" \
                    and ipip["idc"] != "IDC":
                # print("idc: %s, isp: %s, region: %s, city: %s, lon: %s, lat: %s" % (ipip["idc"], ipip["isp"], ipip["region"], ipip["city"], ipip["longitude"], ipip["latitude"]) )
                # print(page_info)

                out.write("%s\n" % json.dumps(page_info))
                count_temp += 1
                if count_temp == save_size:
                    saved_time += 1
                    count_temp = 0
                    out.close()
                    out = open(outfilepath, "a", encoding="utf-8")
                    print("--ind: %d---saved_time: %d---\n" % (ind, saved_time))
                # print("--ind: %d---saved_time: %d---\n"  % (ind, saved_time))
        ind += 1

    out.close()


if __name__ == "__main__":
    pass
    infilepath = "D:\\HTTP数据/全球_HTTP_80/HTTP_80_deviceScanTask_1538017385_80_zgrab.json"
    filter_transaction_us(infilepath, "D:\\data_preprocessed/http_80_us_0.2.json", 11615891)# 838 + 473 saved