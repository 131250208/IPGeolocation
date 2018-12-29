import ner
import time
tagger = ner.SocketNER(host='localhost', port=8080)
from Tools import requests_tools as rt, online_search, other_tools
import settings
from bs4 import BeautifulSoup
import json
import re
from nltk.stem.wordnet import WordNetLemmatizer
import random
import pyprind


def ner_stanford(str):
    '''
    NER tool by Stanford
    :param str:
    :return:
    '''
    try:
        result = tagger.get_entities(str)
    except UnicodeDecodeError:
        return {}

    return result


def filter_out_company_char(str):
    '''
    filter out co., ltd, llc etc.
    :param str:
    :return: cleaner string
    '''
    if str is None or str == "":
        return str

    company_addr = [re.sub("\.", "\.", c) for c in settings.COMPANY_ABBR]
    company_addr = ["(%s)" % c for c in company_addr]
    pattern = r"%s" % "|".join(company_addr)

    org_name = re.sub(pattern, "", str, flags=re.I)

    se = re.search("([0-9a-zA-Z]+.*[0-9a-zA-Z]+)", org_name)
    org_name = se.group(1) if se and se.group(1) is not None else ""
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
    daily_words = json.load(open("../Sources/en_words_list_5000.json", "r"))
    org_name_dict_index = {}
    stop_list = [re.sub("\.", "\.", st) for st in settings.STOP_WORDS]
    for inp_file_path in pyprind.prog_bar(inp_file_path_list):
        org_name_dict = json.load(open(inp_file_path, "r", encoding="utf-8"))#

        # extend
        org_dict_ext = {}

        for org_name in org_name_dict.keys():
            ess_list = generate_org_name_fr_org_full_name(org_name)
            for ess in ess_list:
                if " " not in ess: # if it is a single word
                    lmtzr = WordNetLemmatizer()
                    ori = lmtzr.lemmatize(ess.lower())
                    if ori in daily_words:
                        continue

                if re.match("(%s)" % "|".join(stop_list), ess, flags=re.I):
                    continue

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


def get_relevant_org_names_by_google(org_name):
    '''
    get more relevant org name by search engine(google
    :param query_set:
    :param tag:
    :return: relevant organization name list
    '''
    rel_org_name_set = set()
    text = online_search.google_search(org_name, proxy_type="spider_abroad")
    random.seed(time.time())
    time.sleep(1.5 * random.random())

    soup = BeautifulSoup(text, "lxml")
    # identify the type
    div_kg_hearer = soup.select_one("div.kp-header")

    if div_kg_hearer is None:
        return {"is_org": False, "rel_org": []}

    enti_name = div_kg_hearer.select_one("div[role=heading] span")
    enti_name = enti_name.text if enti_name is not None else None

    span_list = div_kg_hearer.select("span")
    enti_type = span_list[-1].text if len(span_list) > 0 else None

    des = soup.find("h3", text="Description")
    des_info = ""
    if des is not None:
        des_span = des.parent.select_one("span")
        des_info = des_span.text if des_span is not None else ""

    pattern_org = "(%s)" % "|".join(settings.ORG_KEYWORDS)
    se = re.search(pattern_org, enti_type, flags=re.I)
    if se is None:
        return {"is_org": False, "rel_org": []}

    # relevant org name on current page
    a_reltype_list = soup.select("div.MRfBrb > a")
    for a in a_reltype_list:
        rel_org_name_set.add(a["title"].strip())

    # collect next urls
    div_list = soup.select("div.yp1CPe")
    next = []
    host = "https://www.google.com"
    for div in div_list:
        a_list = div.select("a.EbH0bb")
        for a in a_list:
            if "http" not in a["href"]:
                next.append("%s%s" % (host, a["href"]))

    # a_also_search = soup.find("a", text="People also search for")
    # if a_also_search is not None and "http" not in a_also_search["href"]:
    #     next.append("%s%s" % (host, a_also_search["href"]))

    a_parent_org = soup.find("a", text="Parent organization")
    if a_parent_org is not None:
        parent_str = a_parent_org.parent.parent.text.strip()
        parent_org = parent_str.split(":")[1]
        rel_org_name_set.add(parent_org.strip())

    a_subsidiaries = soup.find("a", text="Subsidiaries")
    if a_subsidiaries is not None:
        href = a_subsidiaries["href"]
        if "http" not in href:
            subsidiaries_str = a_subsidiaries.parent.parent.text.strip()
            subs = subsidiaries_str.split(":")[1].split(",")
            for sub in subs:
                sub = sub.strip()
                if sub == "MORE":
                    continue
                rel_org_name_set.add(sub)
            next.append("%s%s" % (host, href))

    # scrawl urls in list 'next'
    for url in next:
        res = rt.try_best_request_get(url, 99, "get_org_name", proxy_type="spider_abroad")
        soup = BeautifulSoup(res.text, "lxml")
        a_list = soup.select("a.klitem")
        for a in a_list:
            rel_org_name = a["title"]
            rel_org_name_set.add(rel_org_name.strip())

        heading_list = soup.select("div.VkpGBb")
        for heading in heading_list:
            heading_str = heading.select_one("div[role='heading']")
            rel_org_name_set.add(heading_str.get_text())

        random.seed(time.time())
        time.sleep(1.5 * random.random())

    rel_org_name_list = [org_name for org_name in rel_org_name_set if len(org_name) > 1]
    return {"is_org": True, "name": enti_name, "type": enti_type, "des": des_info, "rel_org": rel_org_name_list}


def extend_org_name_dict(org_name_dict_file_path):
    try:
        org_name_dict = json.load(open(org_name_dict_file_path, "r", encoding="utf-8"))
    except:
        org_name_dict = {"Baidu": 0, "Google": 0}

    while True:
        org_name_list = [key for key in org_name_dict.keys() if org_name_dict[key] == 0]

        if len(org_name_list) == 0:
            print("ALL DONE!")
            break

        org_name_list = sorted(org_name_list, key=lambda x: len(x))
        for ind, seed in enumerate(org_name_list):
            t1 = time.time()
            rel_org_name_list = get_relevant_org_names_by_google(seed)

            new_org_name_list = [org for org in rel_org_name_list if org not in org_name_dict]
            for org in new_org_name_list:
                org_name_dict[org] = 0

            org_name_dict[seed] = 1  # done
            json.dump(org_name_dict, open(org_name_dict_file_path, "w", encoding="utf-8"))

            print(new_org_name_list)
            print("pro: %d/%d, query:%s, len_new: %d" % (
                ind + 1, len(org_name_list), seed, len(new_org_name_list)))

            t2 = time.time()
            print(t2 - t1)

        random.seed(time.time())
        time.sleep(2 * random.random())


def extract_org_name_fr_copyright(copyright_info):
    # extract fr copyright by RegEx
    owner_info_str = copyright_info
    pattern_cpy = settings.PATTERN_COPYRIGHT
    end_list = ["Inc", "LLC", "L.L.C", "Ltd", "Co.", "All Rights Reserved"]
    pattern_end = "(%s)" % "|".join(end_list)
    pattern_end = re.sub("\.", "\.", pattern_end)
    pattern = "%s+(.*?)%s" % (pattern_cpy, pattern_end)
    se = re.search(pattern, owner_info_str, flags=re.I)

    if se:
        org_name = filter_out_company_char(re.sub("[0-9]{4}", "", se.group(3)))
        if org_name != "":
            return org_name


def extract_org_name_fr_str(target_str, org_name_dict, use_ner=False):
    target_str = target_str.strip()
    if target_str == "":
        return []

    # extract by dict
    words = other_tools.tokenize_v1(target_str)
    candidates = []
    for word in words:
        subset = org_name_dict[word] if word in org_name_dict else []
        if len(subset) == 0:
            continue
        candidates += subset

    winners = []
    for can in set(candidates):
        if can in target_str:
            winners.append(can)

    # # NER Stanford
    # if use_ner and len(winners) == 0:
    #     res_ner = ner_stanford(target_str)
    #     org_list = res_ner["ORGANIZATION"] if "ORGANIZATION" in res_ner else []
    #     if len(org_list) > 0 and len(winners) == 0:
    #         # stanford win
    #         for org in org_list:
    #             open("../Sources/org_name_supplement.txt", "a", encoding="utf-8").write("%s\n" % org)
    #     winners += org_list

    # filer out duplicates
    winners = sorted(winners, key=lambda x: len(x), reverse=True)
    winners_new = []
    mem = ""
    for s in winners:
        if s.lower() not in mem.lower():
            winners_new.append(s)
            mem += " %s" % s
    winners = winners_new

    # list in order
    winners = sorted(winners, key=lambda x: target_str.find(x))

    return winners


def generate_org_name_fr_org_full_name(org_name):
    '''
    extract essential organization name from the full name.
    :param org_name:
    :return:
    '''
    org_name_list = [filter_out_company_char(org_name), ]
    # org_name = re.sub("\(Historical\)", "", org_full_name)

    # extract the abbreviation in "()"
    # pattern = "\([A-Z]{3,}\)"
    # abbr_list = re.findall(pattern, org_name)
    # abbr_list = [re.search("\((.*?)\)", en).group(1) for en in abbr_list]
    # org_name_list += abbr_list

    # filter out (...)
    org_name = re.sub("\(.*?\)", "", org_name)

    # filter out co.,ltd, etc.
    org_name = filter_out_company_char(org_name)
    org_name_list.append(org_name)

    org_name_list = [org for org in set(org_name_list) if org != ""]
    # # split by "," and " - "
    # org_name = re.sub("–", "-", org_name)
    # org_name_list += re.split("\s-\s|,|\s-|-\s|:\s", org_name)

    return org_name_list


def clean_dict(org_name_dict):
    new_dict = {}
    error = ["D.D. Watkins 2008 - Dream Big Workbooks & Content © D.D. Watkins 2011",
             "Copyright | Masterson Method | 123 North Main #5, Fairfield, IA 52556",
             "c) 2012 172.107.177.235"]
    for org_name, val in org_name_dict.items():
        org_name = org_name.strip()
        for err in error:
            if err in org_name:
                print("!")
        if len(org_name) <= 1:
            continue

        pattern_cpy = settings.PATTERN_COPYRIGHT
        end_list = ["Inc", "LLC", "L.L.C", "Ltd", "Co.", "All Rights Reserved"]
        pattern_end = "(%s)" % "|".join(end_list)
        pattern_end = re.sub("\.", "\.", pattern_end)
        pattern = "%s+([^A-Za-z]+)?(.*?)%s" % (pattern_cpy, pattern_end)
        se = re.search(pattern, org_name, flags=re.I)
        if se:
            org_name = filter_out_company_char(se.group(4))
            if org_name is None:
                continue

        new_dict[org_name] = val

    return new_dict


if __name__ == "__main__":
    # f = open("../Sources/org_names/org_names_full_10.json", "r", encoding="utf-8")
    # org_name_dict = json.load(f)
    # print(len(org_name_dict))

    # extend_org_name_dict("../Sources/org_names/org_names_full_10.json")

    org_name_dict = json.load(open("../Sources/org_names/org_names_full_10.json", "r", encoding="utf-8"))
    for org_name in org_name_dict.keys():
        res = get_relevant_org_names_by_google(org_name)
        print(res)

    # for i in range(11):
    #     ori_dict = json.load(open("../Sources/org_names/org_names_full_%d.json" % i, "r", encoding="utf-8"))
    #     new_dict = clean_dict(ori_dict)
    #     print("ori: %d, new: %d" % (len(ori_dict), len(new_dict)))
        # json.dump(new_dict, open("../Sources/org_names/org_names_full_%d.json" % i, "w", encoding="utf-8"))
    pass