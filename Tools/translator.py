import requests
import re
import execjs
import json
import logging
import html
from Tools import settings
import time
import random


tk_calculator = None
js = '''
    function b(a, b) {
        for (var d = 0; d < b.length - 2; d += 3) {
            var c = b.charAt(d + 2),
                c = "a" <= c ? c.charCodeAt(0) - 87 : Number(c),
                c = "+" == b.charAt(d + 1) ? a >>> c : a << c;
            a = "+" == b.charAt(d) ? a + c & 4294967295 : a ^ c
        }
        return a
    }

    function tk(a,TKK) {
        for (var e = TKK.split("."), h = Number(e[0]) || 0, g = [], d = 0, f = 0; f < a.length; f++) {
            var c = a.charCodeAt(f);
            128 > c ? g[d++] = c : (2048 > c ? g[d++] = c >> 6 | 192 : (55296 == (c & 64512) && f + 1 < a.length && 56320 == (a.charCodeAt(f + 1) & 64512) ? (c = 65536 + ((c & 1023) << 10) + (a.charCodeAt(++f) & 1023), g[d++] = c >> 18 | 240, g[d++] = c >> 12 & 63 | 128) : g[d++] = c >> 12 | 224, g[d++] = c >> 6 & 63 | 128), g[d++] = c & 63 | 128)
        }
        a = h;
        for (d = 0; d < g.length; d++) a += g[d], a = b(a, "+-a^+6");
        a = b(a, "+-3^+b+-f");
        a ^= Number(e[1]) || 0;
        0 > a && (a = (a & 2147483647) + 2147483648);
        a %= 1E6;
        return a.toString() + "." + (a ^ h)
    }
    '''
tk_calculator = execjs.compile(js) # use to calculate the token needed for translating request


def req_t_death(method, url, parameters):
    user_agents = [
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
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "referer": "https://translate.google.cn",
    }

    random.seed(time.time())
    headers["user-agent"] = random.choice(user_agents)
    res = None

    if method == "GET":
        if settings.PROXY:
            res = requests.get(url, proxies=get_proxy(), params=parameters, timeout=settings.TIMEOUT)
        else:
            res = requests.get(url, params=parameters, timeout=settings.TIMEOUT)

    elif method == "POST":
        if settings.PROXY:
            res = requests.post(url, data=parameters, headers=headers, timeout=settings.TIMEOUT,
                                proxies=get_proxy())
        else:
            res = requests.post(url, data=parameters, headers=headers, timeout=settings.TIMEOUT)
    return res

def get_TKK():
    '''
    to get a value needed for calculating the token for constructing translating request
    :return: TKK
    '''
    url = "https://translate.google.cn"

    res = req_t_death("GET", url, {})

    TKK = re.search("TKK='(.*?)';", res.text).group(1)
    # TKK = eval('((function(){var a\x3d1440353112;var b\x3d2018945113;return 425716+\x27.\x27+(a+b)})())');
    # print("%s" % (ser.group(1)))
    # mat = re.match(
    #     "\(\(function\(\){var a\\\\x3d(-?\d+);var b\\\\x3d(-?\d+);return (-?\d+)\+\\\\x27\.\\\\x27\+\(a\+b\)}\)\(\)\)",
    #     ser.group(1))
    # print("%s %s %s" % (mat.group(1), mat.group(2), mat.group(3)))
    # r = mat.group(3)
    # a = mat.group(1)
    # b = mat.group(2)
    #
    # TKK = r + '.' + (str(int(float(a) + float(b))))
    return TKK


def trans_req(ori_text, sl="auto", tl="en"):
    '''
    construct translating request
    :param ori_text:
    :param sl:
    :param tl:
    :return:
    '''
    ori_text = html.unescape(ori_text)# unescape the html
    res = None

    while True:
        try:
            tk = tk_calculator.call("tk", ori_text, get_TKK())

            url_trans = "https://translate.google.cn/translate_a/single"

            payload = {
                "client": "t",
                "sl": sl,
                "tl": tl,
                "dt": "t",
                "ie": "UTF-8",
                "oe": "UTF-8",
                "otf": "1",
                "ssel": "0",
                "tsel": "0",
                "kc": "1",
                "tk": tk,
                "q": ori_text,
            }

            res = req_t_death("POST", url_trans, payload)
            print(res.text)
        except Exception as e:
            logging.warning(e)
            logging.warning("error, waiting and try again...")
            logging.warning("original text: %s " % ori_text)
            time.sleep(1)
            continue

        if res.status_code == 200:
            break

    js = None
    try:
        js = json.loads(res.text)
    except Exception as e:
        logging.warning(e)
        return []

    return js

def detect_language(ori_text):
    '''
    identify which language it is
    :param ori_text:
    :return:
    '''
    js = trans_req(ori_text)
    return js[2]


def get_proxy():
    proxy_str = requests.get(settings.PROXY_SPIDER_API).text.strip()
    proxies = {"http": "http://%s" % proxy_str,
               "https": "http://%s" % proxy_str,}
    print(proxies)
    return proxies


def trans(ori_text, sl="auto", tl="en"):
    '''
    translate text that length is less than 5000
    :param ori_text:
    :param sl:
    :param tl:
    :return:
    '''
    js = trans_req(ori_text, sl, tl)
    trans_text = ""
    if js[2] == "en":
        trans_text = js[0][0][0]
    else:
        for pas in js[0]:
            trans_text += pas[0]

    return trans_text


def trans_long(ori_text, sl="auto", tl="en"):
    '''
    split the long text into pieces and translate

    :param ori_text: text whose len > 5000
    :param sl: source language
    :param tl: target language
    :return:
    '''
    stop_char = ["。", ".", ]
    start_flag = 0
    split_marks = []

    pointor = start_flag + 5000 + 1

    while True:
        while ori_text[pointor] not in stop_char:
            pointor -= 1
        split_marks.append(pointor)
        pointor += 5000
        if pointor >= len(ori_text):
            break

    snippets = []
    start_flag = 0
    for m in split_marks:
        snippets.append(ori_text[start_flag:(m + 1)])
        start_flag = m + 1

    if split_marks[-1] != len(ori_text) - 1:
        snippets.append(ori_text[start_flag:len(ori_text)])

    if detect_language(snippets[0]) == "en":
        return ori_text

    en_text = ""
    for sni in snippets:
        en_text += trans(sni)

    return en_text

if __name__ == "__main__":
    pass

    # s = "银行、金融、证券、能源、保险业、采矿、餐饮、宾馆、电讯业、房地产、服务、服装业、公益组织、广告业、航空航天、化学、健康、保健、建筑业、教育、培训、计算机、金属冶炼、警察、消防、会计、美容、媒体、出版、木材、造纸、零售、批发、农业、旅游业、司法、体育运动、学术研究、演艺、医疗服务、艺术、设计、信息技术、音乐舞蹈、运输业、政府机关、机械制造、咨询、林业、汽车"
    # list_industry = s.split("、")
    # print(len(list_industry))
    #
    # records = []
    # for industry in list_industry:
    #     industry = trans(industry)
    #     records.append({
    #         "name_industry": industry,
    #         "fingerprint_code_download_url": "https://www.iotiie.com/fpcode/websitesIden?industry=%s" % industry
    #     })
    #
    # dict_repository = {
    #     "resDBName": "网站类型指纹",
    #     "size": len(list_industry),
    #     "desc": "提供网站类型的识别指纹，在该指纹库中每个类型的网站对应一个指纹的下载链接，下载的对应代码具有指纹识别对应网站类型的能力。",
    #     "records": records
    # }

    # db = json.load(open("../resources/resDB_websites.json", "r"))
    # for r in db["records"]:
    #     industry = r["name_industry"]
    #     list_nw = []
    #     for w in industry.split(" "):
    #         nw = w[0].upper() + w[1:]
    #         list_nw.append(nw)
    #     n_industry = " ".join(list_nw)
    #
    #     r["name_industry"] = n_industry
    #     r["fingerprint_code_download_url"] = r["fingerprint_code_download_url"].split("=")[0] + "=" + n_industry
    #
    # json.dump(db, open("../resources/resDB_websites_0.1.json", "w"))