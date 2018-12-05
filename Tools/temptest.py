from LandmarksCollector import owner_name_extractor as oi
import json
from LandmarksCollector import settings as st_lmc, iterative_inference_machine
from itertools import combinations
from Tools import geo_distance_calculator, network_measurer, settings as st_tool, requests_tools as rt
import random
import pytz
import datetime
import time
import requests
from bs4 import BeautifulSoup
import re

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



if __name__ == "__main__":
    # url = "https://hidemyna.me/en/proxy-list/?country=US&maxtime=1500&type=s#list"

    # !/usr/bin/env python
    import urllib.request

    opener = urllib.request.build_opener(
    urllib.request.ProxyHandler(
            {'http': 'http://lum-customer-hl_95db9f83-zone-static:m6yzbkj85sou@zproxy.lum-superproxy.io:22225'}))
    print(opener.open('http://lumtest.com/myip.json').read())
    print(opener.open("http://www.baidu.com").read())

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
