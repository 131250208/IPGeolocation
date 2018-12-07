from LandmarksCollector import owner_name_extractor as oi
import json
from LandmarksCollector import settings as st_lmc, iterative_inference_machine
from itertools import combinations
from Tools import geo_distance_calculator, network_measurer, settings as st_tool, requests_tools as rt, geoloc_commercial_db, web_mapping_services, other_tools, ner_tool
import random
import pytz
import datetime
import time
import requests
from bs4 import BeautifulSoup
import re
import pyprind


def test_org_extracter():
    landmarks = json.load(open("../Sources/landmarks_planetlab_0.3.json", "r"))
    for lm in landmarks:
        if lm["organization"] == "Palo Alto Research Center":  # Palo Alto Research Center(1.8W)
            print(lm["geo_lnglat"]["pinpointed_area"])
            it = oi.get_org_info_fr_pageinfo(lm["html"], lm["url"])
            while True:
                try:
                    print(next(it))
                except StopIteration:
                    break
            print(lm["url"])


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


def frange(x, y, jump):
    while x < y:
        yield x
        x += jump
    yield y


if __name__ == "__main__":
    # list_lon = list(frange(-125.75583, -66.01197, 0.15))
    # list_lat = list(frange(25.80139, 49.05694, 0.15))
    # coordinates = [{"longitude": lon, "latitude": lat, "done": 0} for lon in list_lon for lat in list_lat]
    #
    # list_lon = list(frange(-125.00583, -66.76197, 0.15))
    # list_lat = list(frange(25.05139, 49.80694, 0.15))
    # coordinates_2 = [{"longitude": lon, "latitude": lat, "done": 0} for lon in list_lon for lat in list_lat]
    # coordinates += coordinates_2
    # print(len(coordinates))
    #
    # chunks = other_tools.chunks_avg(coordinates, 8)
    # for ind, chunk in enumerate(chunks):
    #     json.dump(chunk, open("../Sources/loc/loc_%d.json" % ind, "w"))

    org_dict_t = {}
    for i in range(8):
        org_dict = json.load(open("../Sources/org_names/org_names_full_%d.json" % i, "r"))
        print(len(org_dict))
        org_dict_t = {**org_dict_t, **org_dict}

    print(len(org_dict_t))
    org_list = json.load(open("../Sources/org_names/org_name_list.json", "r"))
    for org in org_list:
        org_dict_t[org] = 0

    org_dict_ext = {}
    for key in org_dict_t.keys():
        ess_list = ner_tool.extract_essentials_fr_org_full_name(key)
        for ess in ess_list:
            org_dict_ext[ess] = 0

    org_dict_t = {**org_dict_t, **org_dict_ext}
    print(len(org_dict_t))

    json.dump(org_dict_t, open("../Sources/org_names/org_name_dict/org_name_dict_1.json", "w"))

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

    pass
