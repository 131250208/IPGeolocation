import json
import requests
from Tools import requests_tools as rt
import re
from bs4 import BeautifulSoup
import socket
import pyprind
from Tools import geolocation, mylogger, online_search, measurement
from LandmarksCollector import settings, org_extracter as oi
logger = mylogger.Logger("../Log/landmarks.py.log")

def crawl_planetlab():
    '''
    crawl landmarks data from planetlab
    :return:
    '''
    res = requests.get("https://www.planet-lab.org/db/pub/sites.php", headers=rt.get_random_headers(),
                       proxies=rt.get_proxies_abroad(), timeout=10)
    soup = BeautifulSoup(res.text, "lxml")
    tbody = soup.select_one("table#sites > tbody")

    landmarks = []
    for tr in tbody.select("tr"):
        td_list = tr.select("td")
        a = td_list[1].select_one("a")
        lon = td_list[2].text
        lat = td_list[3].text
        if a is not None and lon != "" and lat != "":
            url = a["href"]
            organization = td_list[1].text
            landmarks.append({
                "organization": organization,
                "url": url,
                "longitude": lon,
                "latitude": lat,
            })

    return landmarks


def add_locinfo(landmarks_planetlab):
    '''
    add ipinfo into landmarks
    :param landmarks_planetlab:
    :return:
    '''
    count_different = 0
    count_fail = 0
    for lm in pyprind.prog_bar(landmarks_planetlab):
        ip = lm["ip"]

        try:
            json_ipinfo = geolocation.ip_geolocation_ipinfo(ip)
            json_ipip = geolocation.ip_geolocation_ipip(ip)
            city_ipinfo = json_ipinfo["city"]
            region_ipinfo = json_ipinfo["region"]
            country_ipinfo = json_ipinfo["country"]
            city_ipip = json_ipip["city"]
            region_ipip = json_ipip["region"]
            country_ipip = json_ipip["country"]

            loc = json_ipinfo["loc"].split(",")
            lm["ipinfo"] = {
                "city": city_ipinfo,
                "region": region_ipinfo,
                "country": country_ipinfo,
                "longitude": loc[1],
                "latitude": loc[0],
            }
            lm["ipip"] = {
                "city": city_ipip,
                "region": region_ipip,
                "country": country_ipip,
                "longitude": json_ipip["longitude"],
                "latitude": json_ipip["latitude"],
            }

            lm["city"] = ""
            lm["region"] = ""
            lm["country"] = ""

            assert country_ipinfo == "".join(re.findall("[A-Z]", country_ipip))
            lm["country"] = country_ipip

            assert region_ipinfo == region_ipip
            lm["region"] = region_ipip

            assert city_ipinfo == city_ipip
            lm["city"] = city_ipip

        except AssertionError as e:
            count_different += 1
            print("different: %d/%d" % (count_different, len(landmarks_planetlab)))
            # print("different location result, ipinfo: %s, %s, %s; ipip: %s, %s, %s" % (
            #     city_ipinfo, region_ipinfo, country_ipinfo, city_ipip, region_ipip, country_ipip))
        except Exception as e:
            count_fail += 1
            print("fail: %d/%d" % (count_fail, len(landmarks_planetlab)))
            print(e)

    return landmarks_planetlab


def add_html(landmarks):
    '''
    extract html for landmarks that provide web services
    :param landmarks:
    :return:
    '''
    count_fail = 0
    count_suc = 0
    for lm in pyprind.prog_bar(landmarks):
        if "html" in lm and "http-equiv=\"refresh\"" not in lm["html"].lower():
            count_suc += 1
            continue

        url = lm["url"]

        if "html" in lm:
            soup = BeautifulSoup(lm["html"].lower(), "lxml")
            list_meta = soup.select("meta")
            for meta in list_meta:
                if "http-equiv" in meta.attrs and meta["http-equiv"] == "refresh":
                    content = meta["content"]
                    search_group = re.search("url=(.*)", content)
                    if search_group:
                        url_refresh = search_group.group(1)
                        url = rt.recover_url(url, url_refresh)
                        print("refresh: %s" % str(meta))

        if "http" not in url:
            url = "http://www.%s" % url

        # url_split = url.split("//")
        # path = url_split[1]
        # host = re.sub("/.*", "", path)
        # url = url_split[0] + "//" + host

        try:
            res = requests.get(url, proxies=rt.get_proxies_abroad(), headers=rt.get_random_headers(), timeout=30)
            assert res.status_code == 200
            lm["html"] = res.text
            lm["url"] = url
            count_suc += 1
        except Exception as e:
            print(e)
            print("failed: %s" % url)
            count_fail += 1

    print(count_fail)
    print(count_suc)
    return landmarks


def find_ip(landmarks):
    count_fail = 0
    for lm in pyprind.prog_bar(landmarks):
        if "ip" in lm or "url" not in lm:
            continue
        url = lm["url"]

        name = re.sub("http://", "", url)
        name = re.sub("https://", "", name)

        if "/" in name:
            name = name.split("/")[0]

        try:
            ip = socket.gethostbyname(name)
            lm["ip"] = ip
            # print(("getaddrinfo succeed, domain_name: %s, org: %s" % (name, lm["university_name"])))
        except Exception as e:
            count_fail += 1
            # print("getaddrinfo failed, domain_name: %s, org: %s" % (name, lm["university_name"]))
            continue
    print("fail_num: %d" % count_fail)
    return landmarks


def geocode(landmarks_planetlab):
    for lm in pyprind.prog_bar(landmarks_planetlab):
        addr = geolocation.google_map_geocode_co2addr(float(lm["longitude"]), float(lm["latitude"]))
        if addr:
            lm["geo_lnglat"] = addr
    return landmarks_planetlab


def get_candidates_by_page(html, url, lng, lat, radius):
    '''
    construct query string from web page and coarse_grained_region
    :param html:
    :param url:
    :param coarse_grained_region:
    :return: query string
    '''
    candidates = []
    it = oi.get_org_info(html, url)

    last_query = ""
    while True:
        try:
            org_info = next(it)
        except StopIteration:
            break
        query = org_info
        candidates = geolocation.google_map_nearby_search(query, lng, lat, radius)
        last_query = query
        if len(candidates) > 0:
            break

    if len(candidates) > 0:
        return candidates, last_query
    return [], last_query


def get_coordinate_by_commercial_tools(ip):
    ipinfo_fr_ipplus = geolocation.ip_geolocation_ipplus360(ip)  # free trial, one month expire, low precision
    # ipinfo_fr_ipip = geolocation.ip_geolocation_ipip(ip)
    ipinfo_fr_geolite2 = geolocation.ip_geolocation_geolite2(ip)  # free, low precision

    if ipinfo_fr_geolite2["city"] == ipinfo_fr_ipplus["city"] and \
            ipinfo_fr_ipplus["city"] != "":
        coordinates = [{"longitude": ipinfo_fr_ipplus["longitude"],
                        "latitude": ipinfo_fr_ipplus["latitude"]},
                       # {"longitude": ipinfo_fr_ipip["longitude"],
                       #  "latitude": ipinfo_fr_ipip["latitude"]},
                       {"longitude": ipinfo_fr_geolite2["longitude"],
                        "latitude": ipinfo_fr_geolite2["latitude"]},
                       ]
        stdev, exp_coordinate = geolocation.stdev_coordinates(coordinates)
        if stdev <= 10000:
            return {"coarse_grained_region": "%s, %s, %s" %
                                             (ipinfo_fr_geolite2["country"], ipinfo_fr_geolite2["region"], ipinfo_fr_geolite2["city"]),
                    "stdev": stdev,
                    "longitude": exp_coordinate["longitude"], "latitude": exp_coordinate["latitude"]}

    return None


from gevent import monkey; monkey.patch_socket()
import gevent


def search_candidates_ip(page_info, lng_com, lat_com, radius,):
    query_whois = online_search.get_org_name_by_whois_rws(page_info["ip"])
    candidates_fr_whois = geolocation.google_map_nearby_search(query_whois, lng_com, lat_com,
                                                               radius) if query_whois is not None else None

    candidates_fr_page, query_page = get_candidates_by_page(page_info["html"], page_info["url"], lng_com, lat_com,
                                                            radius)

    page_info["result_fr_page"] = {
        "query": query_page,
        "candidates": candidates_fr_page
    }
    page_info["result_fr_whois"] = {
        "query": query_whois,
        "candidates": candidates_fr_whois,
    }
    page_info["result_fr_commercial_tool"] = {
        "longitude": lng_com,
        "latitude": lat_com
    }
    return page_info


def search_candidats(list_page_info):
    '''
    select landmarks from cyberspace
    :param list_page_info: a list of info of web page, including ip, url, html
    :return:
    '''
    count_ambiguity = 0
    radius = 20000

    n = len(list_page_info)
    bar = pyprind.ProgBar(n, track_time=False, title='search_candidats')

    jobs = []
    for ind, page_info in enumerate(list_page_info):
        print("---------------------%d-----------------------" % ind)
        ip = page_info["ip"]
        ipinfo_fr_commercial_tools = get_coordinate_by_commercial_tools(ip) # filter
        if ipinfo_fr_commercial_tools is None:
            count_ambiguity += 1
            print("%s the city is ambiguous..." % ip)
            continue
        lng_com = float(ipinfo_fr_commercial_tools["longitude"])
        lat_com = float(ipinfo_fr_commercial_tools["latitude"])

        jobs.append(gevent.spawn(search_candidates_ip, page_info, lng_com, lat_com, radius))
        bar.update()

    gevent.joinall(jobs)
    list_page_info = [job.value for job in jobs]

    print("count_ambiguity: %d" % count_ambiguity)# count_ambiguity: 1594
    return list_page_info


def select_landmarks(list_inference_info):
    huge_num = 99999999999
    dict_landmark = {}

    for info in list_inference_info:
        ip = info["ip"]
        try:
            lat_com = info["result_fr_commercial_tool"]["latitude"]
            lng_com = info["result_fr_commercial_tool"]["longitude"]
            candidates_fr_whois = info["result_fr_whois"]["candidates"]
            query_whois = info["result_fr_whois"]["query"]
            candidates_fr_page = info["result_fr_page"]["candidates"]
            query_page = info["result_fr_page"]["query"]
            ipinfo_fr_commercial_tools = info["result_fr_commercial_tool"]
        except KeyError:
            continue

        dis_whois2ipip = geolocation.geodistance(lng_com, lat_com, candidates_fr_whois[0]["longitude"],
                                                 candidates_fr_whois[0]["latitude"]) if candidates_fr_whois and len(
            candidates_fr_whois) == 1 else huge_num
        dis_pageinfo2ipip = geolocation.geodistance(lng_com, lat_com, candidates_fr_page[0]["longitude"],
                                                    candidates_fr_page[0]["latitude"]) if candidates_fr_page and len(
            candidates_fr_page) == 1 else huge_num
        dis_page2whois = geolocation.geodistance(candidates_fr_whois[0]["longitude"], candidates_fr_whois[0]["latitude"],
                                                 candidates_fr_page[0]["longitude"], candidates_fr_page[0]["latitude"]) \
            if candidates_fr_page and len(candidates_fr_page) == 1 and candidates_fr_whois and len(candidates_fr_whois) == 1 else huge_num

        # show result
        output = {
            "ip": ip,
            "coordinate_fr_commercial_tools": {
                "longitude": ipinfo_fr_commercial_tools["longitude"],
                "latitude": ipinfo_fr_commercial_tools["latitude"]
            },
            "whois": {
                "query": query_whois,
                "coordinate": candidates_fr_whois,
                "dis_whois2com": dis_whois2ipip,
            },
            "page": {
                "query": query_page,
                "coordinate": candidates_fr_page,
                "dis_page2com": dis_pageinfo2ipip,
            },
            "dis_pageinfo2whois": dis_page2whois,
        }
        logger.war(json.dumps(output, indent=2))

        threshold = 10000
        if dis_whois2ipip <= threshold or dis_pageinfo2ipip <= threshold:
            lng = None
            lat = None
            if dis_pageinfo2ipip < dis_whois2ipip:
                lng = candidates_fr_page[0]["longitude"]
                lat = candidates_fr_page[0]["latitude"]
            else:
                lng = candidates_fr_whois[0]["longitude"]
                lat = candidates_fr_whois[0]["latitude"]
            dict_landmark[ip] = [lng, lat]
    return dict_landmark


def show_results_coordinating_on_planet_lab():
    landmarks = json.load(open("../resources/landmarks_planetlab_0.3.json", "r"))

    count_us = 0
    count_fail = 0
    count_mul = 0
    error_dis = 0
    count = 0
    count_suc = 0
    invalid = []
    for lm in landmarks:
        #     # ------------------------------------------------------
        if "geo_lnglat" not in lm:
            continue
        country = lm["geo_lnglat"]["country"]
        if country == "United States" and "ip" in lm and "html" in lm:

            # if lm["organization"] in settings.INVALID_LANDMARKS:
            #     continue
            if settings.INVALID_LANDMARKS_KEYWORD[0] in lm["organization"] or \
                            settings.INVALID_LANDMARKS_KEYWORD[1] in lm["organization"]:
                # print(lm["organization"])
                # print(lm["url"])
                continue

            area_pinpointed = lm["geo_lnglat"]["pinpointed_area"]

            org = lm["organization"]
            coordi = geolocation.google_map_coordinate(org + " " + area_pinpointed)
            if len(coordi) == 0:
                dis_ground = -1
            else:
                dis_ground = geolocation.geodistance(coordi[0]["lng"], coordi[0]["lat"], float(lm["longitude"]),
                                                     float(lm["latitude"]))
            logger.war("org: %s, res_num:%d, ground_truth_dis: %s" % (org, len(coordi), dis_ground))
            if dis_ground > 3000:
                count_fail += 1
                invalid.append(lm["organization"])
            else:
                count_suc += 1
    print("%s, %s" % (count_suc, count_fail))
    print(invalid)
         # -----------------------------------------------------------------------------------
    #         coordi = []
    #         last_query = ""
    #         it = get_org_info(lm["html"], lm["url"])
    #
    #         query = ""
    #         while True:
    #             try:
    #                 query = next(it)
    #             except StopIteration:
    #                 last_query = query
    #                 break
    #             coordi = geolocation.google_map_coordinate(query + " " + area_pinpointed)
    #             if len(coordi) > 0:
    #                 last_query = query
    #                 break
    #
    #         if len(coordi) == 0:
    #             count_fail += 1
    #             logger.war("--fail... org: %s, query: %s, area: %s" % (org, last_query, area_pinpointed))
    #
    #         elif len(coordi) > 0:
    #             dis_pre = geolocation.geodistance(coordi[0]["lng"], coordi[0]["lat"], float(lm["longitude"]),
    #                                               float(lm["latitude"]))
    #             logger.war("last_query: %s, res_num: %d, pre_dis: %s" % (last_query, len(coordi), dis_pre))
    #             error_dis += dis_pre
    #             if len(coordi) > 1:
    #                 count_mul += 1
    #         count_us += 1
    # logger.war("suc: %d, fail: %d, mul: %d, mean_error_dis: %s" % (count_us - count_fail, count_fail, count_mul, error_dis / (count_us - count_fail)))


if __name__ == "__main__":
    file_inp = open("H:\\Projects/data_preprocessed/pages_with_copyright_us_filtered.json", "r")
    list_page_info = [json.loads(line) for line in file_inp]
    print(len(list_page_info))
    list_page_info = search_candidats(list_page_info)

    json.dump(list_page_info, open("../resources/landmarks_candidates_1.json", "w"))

    # dict_landmarks = select_landmarks(list_page_info)
    # print(json.dumps(dict_landmarks, indent=2))
    # print(len(list(dict_landmarks.keys())))







