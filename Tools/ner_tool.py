import ner
import time
tagger = ner.SocketNER(host='localhost', port=8080)
from Tools import requests_tools as rt, online_search
from bs4 import BeautifulSoup
from gevent import monkey
monkey.patch_socket()
import gevent
from multiprocessing import Pool
import json


def ner_stanford(copyright_info):
    result = tagger.get_entities(copyright_info)
    return result


def extend_org_name(org_name):
    text = online_search.google_search(org_name)
    time.sleep(1)
    soup = BeautifulSoup(text, "lxml")
    div_list = soup.select("div[data-md='133']")
    next = []
    host = "https://www.google.com"
    for div in div_list:
        a_list = div.select("a.EbH0bb")
        for a in a_list:
            next.append("%s%s" % (host, a["href"]))
    a = soup.find("a", text="People also search for")
    if a is not None:
        next.append("%s%s" % (host, a["href"]))

    # res_list = []
    # res_list = [rt.try_best_request_get(url, 5, "get_org_name", "spider") for url in next]
    # pool = Pool(5)
    # for url in next:
    #     res = pool.apply_async(rt.try_best_request_get, args=(url, 5, "get_org_name"))
    #     res_list.append(res)
    # pool.close()
    # pool.join()

    rel_org_name_set = set()
    for url in next:
        # res = res.get()
        res = rt.try_best_request_get(url, 5, "get_org_name",)
        soup = BeautifulSoup(res.text, "lxml")
        a_list = soup.select("a.klitem")
        for a in a_list:
            rel_org_name = a["title"]
            rel_org_name_set.add(rel_org_name)
        time.sleep(1)

    return list(rel_org_name_set)


def update_org_name_db():
    dict_org_name = json.load(open("../Sources/org_names.json", "r"))
    dict_new = {}
    ori_len = len(dict_org_name)
    count = 0
    try:
        for key, val in dict_org_name.items():
            if val == 0:
                org_list = extend_org_name(key)
                for org in org_list:
                    if org not in dict_org_name and org not in dict_new:
                        dict_new[org] = 0
                dict_org_name[key] = 1
                print("%d/%d, query:%s, num: %d, len_new: %d" % (count, ori_len, key, len(org_list), len(dict_new)))
            count += 1
            if count % 100 == 0:
                dict_org_name = {**dict_org_name, **dict_new}
                json.dump(dict_org_name, open("../Sources/org_names_1.json", "w"))
                print("%d org names saved!" % len(dict_org_name))

    except Exception as e:
        dict_org_name = {**dict_org_name, **dict_new}
        json.dump(dict_org_name, open("../Sources/org_names_1.json", "w"))
        print("%d org names saved!" % len(dict_org_name))
        print(e)


if __name__ == "__main__":
    t1 = time.time()
    rel_org_name_list = extend_org_name("Alibaba")
    print(rel_org_name_list)
    print(len(rel_org_name_list))
    print(time.time() - t1)
    # update_org_name_db()

    # org_name_dict = json.load(open("../Sources/org_names.json", "r"))

    pass