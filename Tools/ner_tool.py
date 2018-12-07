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


def filter_out_company_char(str):
    company_addr = [re.sub("\.", "\.", c) for c in st_lan.COMPANY_ABBR]
    company_addr = ["(%s)" % c for c in company_addr]
    pattern = r"%s" % "|".join(company_addr)
    org_name = re.sub(pattern, "", str, flags=re.I)
    org_name = org_name.strip(".")
    org_name = org_name.strip()
    return org_name


def build_indexes(inp_file_path, out_file_path):
    org_name_dict = json.load(open(inp_file_path, "r"))
    org_name_dict_index = {}
    for org_name in org_name_dict.keys():
        word_list = other_tools.tokenize_v1(org_name)
        for word in word_list:
            if len(word) <= 1:
                continue
            if word not in org_name_dict_index:
                org_name_dict_index[word] = set()

            org_name_dict_index[word].add(org_name)

    for key, val in org_name_dict_index.items():
        org_name_dict_index[key] = list(val)

    json.dump(org_name_dict_index, open(out_file_path, "w"))


class OrgNameRecognition:
    def __init__(self, file_path):
        self.dict_org_name = json.load(open(file_path, "r"))

    def get_extended_org_name_list(self, query_list, tag=None):
        rel_org_name_set = set()
        list_done = []
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
                    rel_org_name = filter_out_company_char(rel_org_name)
                    if rel_org_name not in self.dict_org_name:
                        rel_org_name_set.add(rel_org_name)
            list_done.append(query)
            print("tag: %s, pro: %d/%d, query:%s, len_new: %d" % (
            tag, ind + 1, len_qry_list, query, len(rel_org_name_set)))
        return list(rel_org_name_set), list_done

    def update_org_name_db(self, out_path):
        dict_org_name = self.dict_org_name
        org_name_list = list(dict_org_name.keys())
        org_name_list = [org_name for org_name in org_name_list if dict_org_name[org_name] == 0]

        chunks = other_tools.chunks_avg(org_name_list, 8)
        pool = Pool(8)
        res_list = []
        for ind, chunk in enumerate(chunks):
            res = pool.apply_async(self.get_extended_org_name_list, args=(chunk, ind))
            res_list.append(res)
        pool.close()
        pool.join()

        for res in res_list:
            name_list, done_list = res.get()
            for name in name_list:
                self.dict_org_name[name] = 0
            for done in done_list:
                self.dict_org_name[done] = 1

        json.dump(self.dict_org_name, open(out_path, "w"))


org_name_dict = json.load(open("../Sources/org_names/org_name_dict/org_name_dict_index_1.json", "r"))


def org_name_extract(str):
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


def ner_stanford(str):
    result = tagger.get_entities(str)
    return result


def extract_essentials_fr_org_full_name(org_full_name):
    org_name = re.sub("\(Historical\)", "", org_full_name)

    # extract the abbreviation in "()"
    org_name_list_1 = []
    pattern = "\([A-Z]{3,}\)"
    abbr_list = re.findall(pattern, org_name)
    abbr_list = [re.search("\((.*?)\)", en).group(1) for en in abbr_list]
    org_name_list_1 += abbr_list
    org_name = re.sub(pattern, "", org_name)

    # split by "," and " - "
    org_name = re.sub("–", "-", org_name)
    org_name_list_1 += re.split("\s-\s|,|\s-|-\s|:\s", org_name)

    # filter co.,ltd, etc.
    org_name_list_2 = []
    for on in org_name_list_1:
        on = filter_out_company_char(on)
        if on == "":
            continue
        org_name_list_2.append(on)

    # add into list
    essentials = []
    for on in org_name_list_2:
        if len(on) <= 1:
            continue
        essentials.append(on)
    return essentials


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

    # org_name_dict = json.load(open(, "r"))

    # build_indexes("../Sources/org_names/org_name_dict/org_name_dict_1.json", "../Sources/org_names/org_name_dict/org_name_dict_index_1.json")


    # org_name_dict_index = json.load(open("../Sources/org_names/org_name_dict/org_name_dict_index_0.json"))
    # # dict_sta = {}
    # for key, val in org_name_dict_index.items():
    #     if len(val) < 500:
    #         continue
    #     print("key: %s, len: %d" % (key, len(val)))
        # if len(val) not in dict_sta:
        #     dict_sta[len(val)] = 0
        # dict_sta[len(val)] += 1

    # print(json.dumps(dict_sta, indent=2))

    res = org_name_extract("jsdklfjwel ndsf Amazon sjdke eBay Google")
    print(res)
    pass