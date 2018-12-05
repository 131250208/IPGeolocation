import requests
from Tools import settings
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


class MyChrome(webdriver.Chrome):
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % settings.PROXY_ABROAD)
        # chrome_options.add_argument("--headless")
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
    "accept": "*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "Content-Type": "*/*",
}


def get_proxies_spider():
    proxy_str = requests.get(settings.PROXY_SPIDER_API).text.strip()
    proxies = {"http": "http://%s" % proxy_str,
               "https": "http://%s" % proxy_str, }
    return proxies


def get_proxies_abroad():
    proxies = {"http": "http://%s" % settings.PROXY_ABROAD,
               "https": "http://%s" % settings.PROXY_ABROAD}
    return proxies


def get_proxies_spider_abroad():
    ip_port = "lum-customer-hl_95db9f83-zone-static:m6yzbkj85sou@zproxy.lum-superproxy.io:22225"
    proxies = {"http": "http://%s" % ip_port,
               "https": "http://%s" % ip_port}
    return proxies


proxies_dict = {"abroad": get_proxies_abroad(),
                "spider": get_proxies_spider(),
                "spider_abroad": get_proxies_spider_abroad(),
                "None": None}


def get_random_headers():
    random.seed(time.time())
    headers["user-agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0"
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
            res = requests.post(url, data=data, headers=get_random_headers(), proxies=proxies_dict[proxy_type], timeout=10)
            break
        except Exception as e:
            logger.war("reqest in %s went wrong..., tag: %s" % (sys._getframe().f_code.co_name, tag))
            logger.war(e)
            error_count += 1
            if error_count > maxtime:
                logger.war("error_count exceeded: %d, tag: %s" % (maxtime, tag))
                return None
    return res


def try_best_request_get(url, maxtime, tag="-", proxy_type="None"):
    error_count = 0
    while True:
        try:
            res = requests.get(url, headers=get_random_headers(), proxies=proxies_dict[proxy_type], timeout=10)
            break
        except Exception as e:
            logger.war("reqest in %s went wrong..., tag: %s" % (sys._getframe().f_code.co_name, tag))
            logger.war(e)
            random.seed(time.time())
            time.sleep(10 * random.random())
            error_count += 1
            if error_count > maxtime:
                logger.war("error_count exceeded: %d, tag: %s" % (maxtime, tag))
                return None
    return res

if __name__ == "__main__":
    # print(recover_url("http://www.cs.ccu.edu.tw/jjk/mll/jk.html", "home/index.html"))
    pass