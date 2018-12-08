import ner
import time
tagger = ner.SocketNER(host='localhost', port=8080)
from Tools import requests_tools as rt, online_search, other_tools
from LandmarksCollector import settings as st_lan
from bs4 import BeautifulSoup
from gevent import monkey
monkey.patch_socket()
import gevent
from multiprocessing import Pool
import json
import re


def ner_stanford(str):
    '''
    NER tool by Stanford
    :param str:
    :return:
    '''
    result = tagger.get_entities(str)
    return result


def filter_out_company_char(str):
    '''
    filter out co., ltd, llc etc.
    :param str:
    :return: cleaner string
    '''
    company_addr = [re.sub("\.", "\.", c) for c in st_lan.COMPANY_ABBR]
    company_addr = ["(%s)" % c for c in company_addr]
    pattern = r"%s" % "|".join(company_addr)
    org_name = re.sub(pattern, "", str, flags=re.I)

    se = re.search("([0-9a-zA-Z]+.*[0-9a-zA-Z]+)", org_name)
    org_name = se.group(1) if se else ""
    return org_name


def build_indexes_4_org_name_dict(inp_file_path_list):
    '''
    build indexes for organization dict
    :param inp_file_path_list:
            a list of path,
            file format: .json
            content: {"org_name" : 0, ...}
    :param out_file_path:
    :return: new dict
    '''
    org_name_dict_index = {}

    for inp_file_path in inp_file_path_list:
        org_name_dict = json.load(open(inp_file_path, "r"))

        # extend
        org_dict_ext = {}
        for org_name in org_name_dict.keys():
            ess_list = extract_essentials_fr_org_full_name(org_name)
            for ess in ess_list:
                org_dict_ext[ess] = 0

        org_name_dict = org_dict_ext

        # index
        for org_name in org_name_dict.keys():
            word_list = other_tools.tokenize_v1(org_name)
            for word in word_list:
                if word not in org_name_dict_index:
                    org_name_dict_index[word] = set()
                org_name_dict_index[word].add(org_name)

    # transform set to list
    for key, val in org_name_dict_index.items():
        org_name_dict_index[key] = list(val)

    return org_name_dict_index


def extend_org_name_by_google(query_list, tag=None):
    '''
    get more relevant org name by search engine(google
    :param query_list:
    :param tag:
    :return: relevant organization name list
    '''
    rel_org_name_set = set()
    len_qry_list = len(query_list)
    for ind, query in enumerate(query_list):
        text = online_search.google_search(query, "spider_abroad")
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

        for url in next:
            res = rt.try_best_request_get(url, 5, "get_org_name", "spider_abroad")
            soup = BeautifulSoup(res.text, "lxml")
            a_list = soup.select("a.klitem")
            for a in a_list:
                rel_org_name = a["title"]
                rel_org_name_set.add(rel_org_name)
        print("tag: %s, pro: %d/%d, query:%s, len_new: %d" % (
        tag, ind + 1, len_qry_list, query, len(rel_org_name_set)))
    return list(rel_org_name_set)


def update_org_name_db(org_name_list):

    chunks = other_tools.chunks_avg(org_name_list, 8)
    pool = Pool(8)
    res_list = []
    for ind, chunk in enumerate(chunks):
        res = pool.apply_async(extend_org_name_by_google, args=(chunk, ind))
        res_list.append(res)
    pool.close()
    pool.join()


def org_name_extract(str, org_name_dict):
    str = str.strip()
    if str == "":
        return []
    words = other_tools.tokenize_v1(str)
    candidates = []
    for word in words:
        subset = org_name_dict[word] if word in org_name_dict else []
        if len(subset) == 0:
            continue
        candidates += subset

    winners = []
    for can in set(candidates):
        if can in str:
            winners.append(can)
    return winners


def extract_essentials_fr_org_full_name(org_name):
    '''
    extract essential organization name from the full name.
    :param org_name:
    :return:
    '''
    # org_name = re.sub("\(Historical\)", "", org_full_name)

    # extract the abbreviation in "()"
    org_name_list = [filter_out_company_char(org_name), ]
    pattern = "\([A-Z]{3,}\)"
    abbr_list = re.findall(pattern, org_name)
    abbr_list = [re.search("\((.*?)\)", en).group(1) for en in abbr_list]
    org_name_list += abbr_list

    # filter out (...)
    org_name = re.sub("\(.*?\)", "", org_name)

    # filter out co.,ltd, etc.
    org_name = filter_out_company_char(org_name)
    if org_name != "":
        org_name_list.append(org_name)

    # # split by "," and " - "
    # org_name = re.sub("–", "-", org_name)
    # org_name_list += re.split("\s-\s|,|\s-|-\s|:\s", org_name)

    return org_name_list


# onr = OrgNameRecognition("../Sources/org_names_1.json")
#
#
# def org_name_extract(str):
#     dict_str = onr.get_dict_str()
#     lcsubstr, ind_start, ind_end = other_tools.find_lcsubstr(dict_str, str)
#     pre_c = dict_str[ind_start - 1]
#     follow_c = dict_str[ind_end]
#     if pre_c == "^" and follow_c == "^":
#         return lcsubstr
#     else:
#         return None


if __name__ == "__main__":
    # path = "../Sources/org_names_1.json"
    # onn = OrgNameRecognition(path)
    # t1 = time.time()
    # rel_org_name_list = onn.get_extended_org_name_list(["Baidu", "Google", ])
    # print(rel_org_name_list)
    # print(len(rel_org_name_list))
    # print(time.time() - t1)

    # print(org_name_extract("Amazon"))
    # onn.update_org_name_db("../Sources/org_names_2.json")

    # org_name_dict_index = json.load(open(, "r"))

    # path_list = ["../Sources/org_names/org_names_full_%d.json" % i for i in range(10)]
    # org_name_dict_index = build_indexes_4_org_name_dict(path_list)
    # json.dump(org_name_dict_index, open("../Sources/org_names/org_name_dict_index/org_name_dict_index_0.json", "w"))

    # org_name_dict_index = json.load(open("../Sources/org_names/org_name_dict_index/org_name_dict_index_0.json"))
    # # dict_sta = {}
    # for key, val in org_name_dict_index.items():
    #     if len(val) < 500:
    #         continue
    #     print("key: %s, len: %d" % (key, len(val)))
        # if len(val) not in dict_sta:
        #     dict_sta[len(val)] = 0
        # dict_sta[len(val)] += 1

    # print(json.dumps(dict_sta, indent=2))

    org_name_dict = json.load(open("../Sources/org_names/org_name_dict_index/org_name_dict_index_0.json", "r"))
    res = org_name_extract("Harvard University jsdklfj DDM global wel Tofino Brewing Company ndsf Amazon sjdke eBay Google", org_name_dict)
    print(res)
    pass