import json
from Tools import geo_distance_calculator, geoloc_commercial_db, web_mapping_services, network_measurer
import time
import requests
from bs4 import BeautifulSoup
import re
import pyprind
import strings


def test_copyright():
    pass
    # landmarks = json.load(open("../Sources/landmarks_planetlab_0.3.json", "r"))
    # for lm in landmarks:
    #     if lm["organization"] in settings.INVALID_LANDMARKS:
    #         continue
    #     if settings.INVALID_LANDMARKS_KEYWORD[0] in lm["organization"] or \
    #                     settings.INVALID_LANDMARKS_KEYWORD[1] in lm["organization"]:
    #         continue
    #         # ------------------------------------------------------
    #     if "geo_lnglat" not in lm:
    #         continue
    #     country = lm["geo_lnglat"]["country"]
    #     if country == "United States" and "ip" in lm and "html" in lm:
    #         soup = purifier.get_pure_soup_fr_html(lm["html"])
    #         list_copyright_info = oi.extract_copyright_info(soup)
    #         list_org_fr_copyright = oi.extract_org_fr_copyright(list_copyright_info)
    #         print("list_cpyinfo_raw: %s, list_cpy: %s" % (list_copyright_info, list_org_fr_copyright))

def extract_state_names():
    url = "http://www.fltacn.com/article_177.html"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html5lib")
    table = soup.select_one("div.article table")
    tr_list = table.select("tr")[1:]
    list_sta = []
    list_abbr = []
    for tr in tr_list:
        td_list = tr.select("td")
        state_name = td_list[1].text.strip()
        state_name = re.sub("[\s\t\n\r]+", " ", state_name)
        list_sta.append(state_name)
        abbreviation = td_list[2].text.strip()
        list_abbr.append(abbreviation)
    print(json.dumps(list_sta))
    print(json.dumps(list_abbr))


def extract_org_names_batch(ip_dict_path, org_name_dict_path):
    ip_dict = json.load(open(ip_dict_path, "r"))
    try:
        org_name_dict = json.load(open(org_name_dict_path, "r"))
    except Exception:
        org_name_dict = {}

    ip_list = [ip for ip in ip_dict.keys() if ip_dict[ip] == 0]
    try:
        for ip in ip_list:
            locations = geoloc_commercial_db.get_locations_info_by_commercial_tools(ip)
            location_list = [locations["ipip"], locations["ipplus"], locations["geolite2"],]
            location_list = geo_distance_calculator.merge_near_locations(location_list, 20000)
            query_list = ["company", "institution", "organization", "school", "university", "academic", "government"]
            for loc in location_list:
                for query in query_list:
                    org_list = web_mapping_services.google_map_nearby_search(query, loc["longitude"], loc["latitude"], 50000)
                    for org in org_list:
                        org_name = org["org_name"]
                        if org_name not in org_name_dict:
                            org_name_dict[org_name] = 0
            ip_dict[ip] = 1
    except Exception:
        json.dump(ip_dict, open(ip_dict_path, "w"))
        json.dump(org_name_dict, open(org_name_dict_path, "w"))


def get_loc_list(ip_dict_path, loc_list_path):
    ip_dict = json.load(open(ip_dict_path, "r"))
    ip_list = [ip for ip in ip_dict.keys() if ip_dict[ip] == 0]
    loc_list_total = []
    len_ip_list = len(ip_list)
    for ind, ip in enumerate(ip_list[:1000]):
        locations = geoloc_commercial_db.get_locations_info_by_commercial_tools(ip)
        loc_list_total.append(locations["ipip"])
        loc_list_total.append(locations["ipplus"])
        loc_list_total.append(locations["geolite2"])
        # location_list = [locations["ipip"], locations["ipplus"], locations["geolite2"], ]
        # loc_list_total += location_list
        print("loc_pro: %d/%d" % (ind + 1, len_ip_list))

    t1 = time.time()
    loc_list_total = geo_distance_calculator.merge_near_locations(loc_list_total, 20000)
    print(time.time() - t1)
    print("ip_num: %d, loc_num: %d" % (len_ip_list, len(loc_list_total)))
    json.dump(loc_list_total, open(loc_list_path, "w"))


# ----------------
import sys, getopt

if __name__ == "__main__":
    # samples = json.load(open("../Sources/experiments/samples_planetlab_us_0.1.json", "r", encoding="utf-8"))
    # print(len(samples))
    # count_valid = 0
    # for sample in samples:
    #     if sample[strings.KEY_DIS_COARSE_LOC_2_GROUND] > 15000:
    #         continue
    #     count_valid += 1
    #
    # print(count_valid)

    # count_single = 0
    # for sample in pyprind.prog_bar(samples):
    #     url = sample["url"]
    #     host = re.search("https?://(.*?)/?", sample["url"]).group(1)
    #     ips = network_measurer.get_all_ips(host)
    #     if len(ips) == 1:
    #         count_single += 1
    #
    # print(count_single)
    import ijson

    filename = "H:\\poi-data/asia.poi.json"
    with open(filename, 'r', encoding="utf-8") as f:
        objects = ijson.items(f, 'features.item')
        item1 = dict(next(objects))
        print(json.dumps(item1, indent=2))

    '''
    cities
    '''
    from itertools import islice
    import csv
    # query_seed_dict_cities = {}
    #
    # cities_file = open("../Sources/city.txt", "r", encoding="utf-8")
    # for c in cities_file:
    #     query_seed_dict_cities[c.strip()] = 0
    # print(len(query_seed_dict_cities))

    # with open("../Sources/worldcities.csv", 'r', encoding="utf-8") as csvfile, \
    #     open("../Sources/city_lon_lat.json", "r", encoding="utf-8") as cities_json, \
    #     open("../Sources/world_cities_new.csv", "w", encoding="utf-8") as csvout:
    #     reader = csv.reader(csvfile)
    #     writer = csv.writer(csvout)
    #     cities = json.load(cities_json)
    #     for row in reader:
    #         if reader.line_num == 1:
    #             writer.writerow(row)
    #             continue
    #         city_name = row[0]
    #         country = row[5]
    #         region = row[8]
    #         latitude = float(row[3])
    #         longitude = float(row[4])
    #
    #         for city in cities:
    #             if city_name == city["cityName"] and country == city["country"] and region == city["province"]:
    #                 row[3] = str(city["lat"])
    #                 row[4] = str(city["lon"])
    #
    #         writer.writerow(row)
    #         print("line: {}".format(reader.line_num))


    #
    # json.dump(query_seed_dict_cities, open("../Sources/query_seed_dict_google_cloud_city.json", "w", encoding="utf-8"))

    '''
    update seed and prepare dict for building
    '''
    from DictBuilder import dict_builder

    # query_seed_dict = json.load(open("../Sources/org_names/query_seed_dict.json", "r", encoding="utf-8"))

    # entity_list = json.load(open("../Sources/org_names/entity_list.json", "r", encoding="utf-8"))
    #
    # org_name_dict = dict_builder.entity_list_2_org_name_dict(entity_list)
    # count_done = 0
    # print(len(org_name_dict))
    #
    # json.dump(org_name_dict, open("../Sources/org_names/org_name_dict_0.json", "w", encoding="utf-8"))

    '''
    translation
    '''
    # from Doraemon.OnlineSearch import google_translator
    # from Doraemon.Requests import requests_dora
    # query_dict = json.load(open("../Sources/org_names/org_name_dict_0.json", "r", encoding="utf-8"))
    # query_list = [query for query in query_dict.keys()]
    # query_str = ". ".join(query_list)
    # trans_str = google_translator.trans_long(query_str, tl="zh-TW")



    # from Cities import cities_retriever
    # cr = cities_retriever.CitiesRetriever("../Sources/dict_1.json")
    # res = cr.retrieve_cities(98.51645342450165, 134.6121719570356, 21.087408226557084, 42.72426491686815, 10000)
    # print(res)

    '''
    indirect delay
    '''
    # rt1 = network_measurer.traceroute("67.169.33.195")
    # # rt2 = network_measurer.traceroute("67.168.32.196")
    # for i in range(254):
    #     addr = i + 2
    #     rt2 = network_measurer.traceroute("67.168.32.{}".format(addr))
    #     print(iterative_inference_machine.get_indirect_route(rt1, rt2))
    # print(requests.get("https://www.bing.com").text)

    '''
    download probes on RIPE
    '''
    # ripe_account = settings.RIPE_ACCOUNT_KEY[0]
    # ripe = network_measurer.RipeAtlas(ripe_account["account"], ripe_account["key"])
    # ip_2_loc_ripe = ripe.get_all_probes_us()
    # json.dump(ip_2_loc_ripe, open("../Sources/landmarks_ripe_us.json", "w", encoding="utf-8"))

    '''
    test our dict compared to NER stanford
    '''
    # org_name_dict = json.load(open("../Sources/org_names/org_name_dict_index/org_name_dict_index_1.json", "r"))
    # str = "sdfsdkfl VECTOR ;sk,dw[eo Licess [.v/x  d Ubuntu sfrrwr sdfdsgf rth Johns Hopkins University dafg Harvard University jsd Apache klfj DDM global wel Tofino Brewing Company ndsf Amazon sjdke eBay Google"
    # # str = "Silverthorne Seismic, LLC Silverthorne Seismic, LLC Silverthrone SILVERTHRONE silverthrone Copyright © 2018 Silverthorne Seismic, LLC , "
    #
    # res = ner_tool.extract_org_name_fr_str(str, org_name_dict)
    # print(res)
    # res = ner_tool.ner_stanford(str)
    # print(res)

    # t1 = time.time()
    # for i in range(1000):
    #     res = ner_tool.extract_org_name_fr_str(str, org_name_dict)
    # t2 = time.time()
    # print("%f" % (t2 - t1))
    #
    # for i in range(1000):
    #     res = ner_tool.ner_stanford(str)
    # t3 = time.time()
    # print("%f" % (t3 - t2))


    # samples = json.load(open("../Sources/experiments/samples_planetlab_us.json", "r", encoding="utf-8"))
    # dataset_dict = {}
    # for sample in samples:
    #     dataset_dict[sample["ip"]] = sample
    #
    # json.dump(dataset_dict, open("../Sources/experiments/dataset_planetlab_us_dict.json", "w", encoding="utf-8"))

    '''
    extend the coverage by /24 cluster
    '''
    # landmark_dict = json.load(open("../Sources/landmarks/landmarks_fr_cyberspace_2.json", "r", encoding="utf-8"))
    # landmark_dict_extended = {}
    # for ip, loc in landmark_dict.items():
    #     key = ".".join(ip.split(".")[:-1])
    #     if key not in landmark_dict_extended:
    #         landmark_dict_extended[key] = []
    #     landmark_dict_extended[key].append(loc)
    # json.dump(landmark_dict_extended, open("../Sources/landmarks/landmarks_extended_2.json", "w", encoding="utf-8"))
    #
    # for key, loc_list in landmark_dict_extended.items():
    #     print("-------key: %s, len: %d-------" % (key, len(loc_list)))
    #
    # print(len(landmark_dict_extended))
    # print(len(landmark_dict_extended) * 256)

    '''
    RegEx for extracting org name in copyright info
    '''
    # st_list = ["Silverthorne Seismic, LLC Silverthorne Seismic, LLC Silverthrone SILVERTHRONE silverthrone Copyright © 2018 Silverthorne Seismic, LLC , ",
    #            "'Development - Login OS Os os © OutSystems. All rights reserved.'",
    #            "© 1997-2013 Shirlene. All rights reserved worldwide.,",
    #            "Copyright © 2018. APC Technology Group. All Rights Reserved., ",
    #            "©1995-2004 Macromedia, Inc. All rights reserved.",
    #             "©2004 Microsoft Corporation. All rights reserved.",
    #             "Copyright © 2004 Adobe Systems Inc.",
    #             "(c)1995-2004 Eric A. and Kathryn S. Meyer. All Rights Reserved.",
    #            "More than just a vision board! Dream Big Collection Home Dream Big TM, Dream Big Vision Books © D.D. Watkins 2008 - Dream Big Workbooks & Content ",
    #            "sdfsdf© D.D. Watkins 2011 - all rights reserved - Patent 2012-AP"]
    # for st in st_list:
    #     print(ner_tool.extract_org_name_fr_copyright(st))


    # print(re.search("([0-9]{4}[\s\-]*([0-9]{4})*)", "2018").group(1))

    # dis = geo_distance_calculator.get_geodistance_btw_2coordinates(-125.75583, 25.80139, -125.75583, 25.85139)
    # print(dis)

    # import enchant
    # d = enchant.Dict("en_US")
    # print(d.check("Hello"))

    # l = ["Stacked", "Books", "Archives", "cars"]
    #
    # from nltk.stem.wordnet import WordNetLemmatizer
    # lmtzr = WordNetLemmatizer()
    # for w in l:
    #     res = lmtzr.lemmatize(w.lower())
    #     print(res)

    # sch_list = json.load(open("../Sources/schools_us_0.5.json", "r"))
    # uni_list = json.load(open("../Sources/universities_us_0.8.json", "r"))
    # planet_list = json.load(open("../Sources/landmarks_planetlab_raw.json", "r"))
    # org_name_dict_index = {}
    # for sch in sch_list:
    #     org_name_dict_index[sch["school_name"]] = 0
    # for uni in uni_list:
    #     org_name_dict_index[uni["university_name"]] = 0
    # for en in planet_list:
    #     org_name_dict_index[en["organization"]] = 0
    # print(len(org_name_dict_index))
    # json.dump(org_name_dict_index, open("../Sources/org_names/org_names_full_9.json", "w"))

    # print(re.split("\s(-)\s|,|\s-|-\s|:\s", "dfsd -df, sdfs–dfsd - df: sdfsd"))

    # url = "https://hidemyna.me/en/proxy-list/?country=US&maxtime=1500&type=s#list"

    # !/usr/bin/env python
    # import urllib.request
    #
    # opener = urllib.request.build_opener(
    # urllib.request.ProxyHandler(
    #         {'http': 'http://lum-customer-hl_95db9f83-zone-static:m6yzbkj85sou@zproxy.lum-superproxy.io:22225'}))
    # # print(opener.open('http://lumtest.com/myip.json').read())
    # print(opener.open("https://www.google.com").read())

    # probes = json.load(open("../Sources/landmarks_ripe_us.json", "r"))
    # dict_landmarks = json.load(open("../Sources/landmarks_fr_cyberspace_1.json", "r"))
    # dict_landmarks_4_training = {}
    #
    # import pyprind
    # for pb in pyprind.prog_bar(probes.values()):
    #     for key, val in dict_landmarks.items():
    #         dis = geo_distance_calculator.get_geodistance_btw_2coordinates(pb["longitude"], pb["latitude"], val["longitude"], val["latitude"])
    #         if dis <= 1000:
    #             dict_landmarks_4_training[key] = val
    #
    # print(len(dict_landmarks_4_training)) # 12827


    # random.shuffle(probe_list)
    #
    # pair_list = list(combinations(probe_list, 2))
    # dis_min = 999999999
    # pair_closest = None
    # for pair in pair_list:
    #     dis = geo_distance_calculator.get_geodistance_btw_2coordinates(pair[0]["longitude"], pair[0]["latitude"], pair[1]["longitude"], pair[1]["latitude"])
    #     if dis < dis_min:
    #         dis_min = dis
    #         pair_closest = pair
    #
    # random.shuffle(probe_list)
    # pb = probe_list[0]
    #
    # print(dis_min)
    # print(pair_closest)
    # print(pb)

    # target_list = [{'ip': '67.169.33.196', 'longitude': -121.8895, 'latitude': 37.3415}, {'ip': '162.231.243.83', 'longitude': -121.8895, 'latitude': 37.3415}, {'ip': '67.82.50.43', 'longitude': -73.6315, 'latitude': 40.7305}]
    # target_list = [pair_closest[0], pair_closest[1], pb]
    # target_list = ["67.169.33.196", "162.231.243.83", "67.82.50.43"]
    # random.shuffle(probe_list)
    # pb_list = [str(prb["id"]) for prb in probe_list[:25]]
    #
    # account = st_tool.RIPE_ACCOUNT_KEY[0]
    # ripe = network_measurer.RipeAtlas(account["account"], account["key"])
    # zone = pytz.country_timezones('us')[0]
    # tz = pytz.timezone(zone)
    # start_time = datetime.datetime.now(tz).timestamp() + 120
    #
    # res = ripe.measure_by_ripe_oneoff_ping(target_list, pb_list, start_time, ["2018130-cs", ], "check similarity")
    # print(res)
    # print(res.text)

    # str = ",.. sdfasdfIJNINS08iOF , JIOWE , .; "
    # se = re.search("([0-9a-zA-Z]+.*[0-9a-zA-Z]+)", str)
    # print(se.group(1))
    pass
