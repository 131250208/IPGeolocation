import requests
import settings
import random
import time
import re
from Tools import mylogger
import sys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
logger = mylogger.Logger("../Log/request_tools.py.log")
import json


class MyChrome(webdriver.Chrome):

    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % settings.PROXY_LOC_SHADOW)
        chrome_options.add_argument("--headless")
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option('prefs', prefs)
        super(MyChrome, self).__init__(options=chrome_options)

    # def get_chrome(self):
    #     return self.chrome

    def wait_to_get_element(self, css_selector):
        while True:
            try:
                element = WebDriverWait(self, settings.DRIVER_WAITING_TIME).until(
                    ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
                break
            except Exception as e:
                print(e)
                continue
        return element


user_agents = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533+ (KHTML, like Gecko) Element Browser 5.0",
    "IBM WebExplorer /v0.94", "Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
    "Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14",
    "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
    "Opera/8.0 (Windows NT 5.1; U; en)",
    "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
]
headers = {
    "host": "www.google.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    # "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "referer": "www.google.com",
}


def get_proxies_spider():
    proxy_str = requests.get(settings.PROXY_DATA5U_SPIDER_API).text.strip()
    proxies = {"http": "http://%s" % proxy_str,
               "https": "http://%s" % proxy_str, }
    return proxies


def get_proxies_abroad():
    pro = settings.PROXY_LOC_SHADOW
    proxies = {"http": "http://%s" % pro,
               "https": "http://%s" % pro}
    return proxies


def get_proxies_luminati():
    proxy = "lum-customer-hl_95db9f83-zone-static:m6yzbkj85sou@zproxy.lum-superproxy.io:22225"
    proxies = {"http": "http://%s" % proxy,
               "https": "https://%s" % proxy, }
    return proxies


def get_proxies(type):
    if type == "abroad":
        return get_proxies_abroad()
    elif type == "spider":
        return get_proxies_spider()
    elif type == "spider_abroad":
        return get_proxies_luminati()
    else:
        return None


def get_random_headers():
    random.seed(time.time())
    # headers["user-agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0"
    headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
    return headers


def recover_url(url_this, path):
    '''
    recover uncompleted path, like: ../index.html, ./index.html, /index.html, index/html, //webmedia.ku.edu/templates/2012/images/ku_sig_logo.png
    :param url_this:
    :param path:
    :return:
    '''
    url_this = url_this[:-1] if url_this[-1] == "/" else url_this
    if path == "":
        return path

    url_split = url_this.split("//")
    path_this = url_split[1]
    host = re.sub("/.*", "", path_this)
    host = url_split[0] + "//" + host

    pattern_backup = re.compile("\.\./")
    pattern_current = re.compile("\./")
    count_backup = len(pattern_backup.findall(path))
    if "http" in path:
        return path

    if count_backup > 0:
        components_host = url_this.split("/")
        path = re.sub("\.\./", "", path)
        return "/".join(components_host[:-(count_backup + 1)]) + "/" + path

    if len(pattern_current.findall(path)) > 0:
        path = re.sub("\./", "", path)
        return url_this + "/" + path

    if len(path) <= 2:
        return path

    if path[:2] == "//":
        return url_split[0] + path

    if path[0] != "/":
        path = "/" + path
    return host + path


def try_best_request_post(url, data, maxtime, tag="-", proxy_type="None"):
    error_count = 0
    while True:
        try:
            res = requests.post(url, data=data, headers=get_random_headers(), proxies=get_proxies(proxy_type), timeout=10)
            break
        except Exception as e:
            logger.war("reqest in %s went wrong..., tag: %s" % (sys._getframe().f_code.co_name, tag))
            logger.war(e)
            error_count += 1
            if error_count > maxtime:
                logger.war("error_count exceeded: %d, tag: %s" % (maxtime, tag))
                return None

    if res is None or res.status_code != 200:
        return None
    if res.text is None or res.text.strip() == "":
        return None

    return res


def try_best_request_get(url, maxtime, tag="-", proxy_type="None"):
    error_count = 0
    while True:
        try:
            res = requests.get(url, headers=get_random_headers(), proxies=get_proxies(proxy_type), timeout=10)
            break
        except Exception as e:
            logger.war("reqest in %s went wrong..., tag: %s" % (sys._getframe().f_code.co_name, tag))
            logger.war(e)
            random.seed(time.time())
            time.sleep(5 + 10 * random.random())
            error_count += 1
            if error_count > maxtime:
                logger.war("error_count exceeded: %d, tag: %s" % (maxtime, tag))
                return None

    if res is None or res.status_code != 200:
        return None
    if res.text is None or res.text.strip() == "":
        return None
    return res


if __name__ == "__main__":
    import urllib.request

    url_lum = "http://lumtest.com/myip.json"
    url_google = "https://www.google.com"
    url_baidu = "https://ipv6.baidu.com"
    url_facebook = "https://www.facebook.com"
    url_facebook_4 = "https://31.13.82.1"
    url_youtube = "https://www.youtube.com/"
    # query = "Alibaba"
    # url_query = 'https://www.google.com/search?biw=1920&safe=active&hl=en&q=%s&oq=%s' % ("ip", "ip")

    # opener = urllib.request.build_opener(
    #     urllib.request.ProxyHandler(
    #         {'http': 'http://217.29.62.222:24515:N0ax4w:EjJ3EE'}))
    # print(opener.open('http://lumtest.com/myip.json').read())

    res = try_best_request_get(url_google, 5, proxy_type="spider")

    print(res.text)

    # import urllib.request
    # import random
    #
    # url_google = "https://www.google.com"
    # username = 'lum-customer-hl_95db9f83-zone-zone1-route_err-pass_dyn'
    # password = '1bgiacxdl2xa'
    # port = 22225
    # session_id = random.random()
    # super_proxy_url = ('http://%s-session-%s:%s@zproxy.lum-superproxy.io:%d' %
    #                    (username, session_id, password, port))
    # proxy_handler = urllib.request.ProxyHandler({
    #     'http': super_proxy_url,
    #     'https': super_proxy_url,
    # })
    # opener = urllib.request.build_opener(proxy_handler)
    # opener.addheaders = \
    #     [('User-Agent', 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0')]
    # print('Performing request')
    # print(opener.open(url_google).read())

    # import urllib.request
    #
    # opener = urllib.request.build_opener(
    #     urllib.request.ProxyHandler(
    #         {'https': 'https://lum-customer-hl_95db9f83-zone-zone1:1bgiacxdl2xa@zproxy.lum-superproxy.io:22225'}))
    # print(opener.open(url_query).read())
    pass