import logging
from bs4 import BeautifulSoup
import json
import re

def is_valid(sample):
    '''

    :param sample:
    :param filter_pos: filter positive samples? -> check title and content by key words?
    :return:
    '''

    if sample.strip("\n") == "":
        return False

    # filter json loading fail
    try:
        web_page = json.loads(sample)
    except Exception as e:
        logging.warning(e)
        logging.warning("error str can not be loads as json: %s" % sample)
        return False

    if "error" in web_page:  # filter error pages
        return False

    # filter samples without status code
    try:
        status_code = web_page["data"]["http"]["response"]["status_code"]
    except Exception as e:
        logging.warning(e)
        logging.warning("has no status_code: %s" % sample)
        return False

    if status_code != 200:  # filter pages of which status code is not 200
        return False

    en = get_brief_one(sample)
    if en is None:
        return False

    return True


def get_brief_one(sample):
    '''

    :param sample:
    :return:
    '''
    try:
        web_page = json.loads(sample)
    except Exception as e:
        logging.warning(e)
        return None

    ip = web_page["ip"]
    response = web_page["data"]["http"]["response"]
    if "body" in response:
        html = response["body"]
    else:
        return None

    if html.strip() == "":
        return None

    try:
        title = ""
        soup = BeautifulSoup(html, "lxml")
        tag_title = soup.select_one("title")
        if tag_title is not None:
            title = tag_title.get_text()
        else:
            match = re.search("<title[^>]*>(.*)</title>", html)
            if match is not None:
                title = match.group(1)

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
                "host": "%s://%s" % (scheme, host),
                }
    except Exception as e:
        logging.warning(e)
        return None # if no url(scheme, host, path) in sample, return None, FYI, sometimes title can be "".