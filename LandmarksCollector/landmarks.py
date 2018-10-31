import json
import requests
from Tools import requests_tools as rt
import re
from bs4 import BeautifulSoup
import socket
import pyprind
from Tools import geolocation, mylogger
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


def find_ip(landmarks_planetlab):
    count_fail = 0
    for lm in pyprind.prog_bar(landmarks_planetlab):
        url = lm["url"]

        name = re.sub("http://", "", url)
        name = re.sub("https://", "", name)

        if "/" in name:
            name = name.split("/")[0]

        map_err2cor = {"minarlab.mis.npust.edu.": "minarlab.mis.npust.edu.tw",
                       "www.xjtu.edu.cn:8080": "www.xjtu.edu.cn",
                       }
        if name in map_err2cor:
            name = map_err2cor[name]

        try:
            ip = socket.gethostbyname(name)
            lm["ip"] = ip
        except Exception as e:
            count_fail += 1
            print("getaddrinfo failed, failname: %s, org: %s" % (name, lm["organization"]))
            continue
    return landmarks_planetlab


def geocode(landmarks_planetlab):
    for lm in pyprind.prog_bar(landmarks_planetlab):
        addr = geolocation.google_map_geocode_co2addr(float(lm["longitude"]), float(lm["latitude"]))
        if addr:
            lm["geo_lnglat"] = addr
    return landmarks_planetlab


def get_all_lm():
    map_ip_coordinate = {}
    data = []
    # landmarks = json.load(open("../resources/landmarks_planet_lab_us.json", "r"))
    # for lm in landmarks:
    #     map_ip_coordinate[lm["ip"]] = [lm["longitude"], lm["latitude"]]
    #     data.append({"name": lm["ip"], "value": 200})

    # file_probes = open("../resources/probes.txt", "r")
    # list_probe_id = []
    # for line in file_probes:
    #     pro_id = re.search("(\d+)", line).group(1)
    #     list_probe_id.append(pro_id)
    # list_probe_id = ["35151", "13191", "33713", "34726", "14750", "10693", "3588", "14606"] # 8
    #
    # url = "https://atlas.ripe.net:443/api/v2/probes/?id__in=%s" % ",".join(list_probe_id)

    url = "https://atlas.ripe.net:443/api/v2/probes/?country_code=US&status=1"

    while True:
        res = requests.get(url)
        print("req: %s" % url)
        probes = json.loads(res.text)

        for r in probes["results"]:
            ip = r["address_v4"]
            # id = r["id"]
            if ip is not None:
                coordinates = r["geometry"]["coordinates"]
                map_ip_coordinate[ip] = coordinates  # [lon, lat]
                data.append({"name": ip, "value": 50})

        next_page = probes["next"]
        if next_page is None:
            break
        else:
            url = next_page

    print(json.dumps(map_ip_coordinate))
    print("-------------------------")
    print(json.dumps(data))
    return map_ip_coordinate


def get_coordination_by_page(html, url, area):
    coordi = []
    it = oi.query_str(html, url)

    last_query = ""
    while True:
        try:
            query = next(it)
            last_query = query
        except StopIteration:
            break
        coordi = geolocation.google_map_coordinate(query + " " + area)
        logger.info("query: %s" % query)
        if len(coordi) > 0:
            last_query = query
            break
    logger.war("last_query: %s" % last_query)
    if len(coordi) > 0:
        return coordi[0]
    return None


if __name__ == "__main__":
    file_inp = open("E:\\data_preprocessed/http_80_us.json", "r")
    for line in file_inp:
        if line != "\n":
            json_pageinfo = json.loads(line)
            ip = json_pageinfo["ip"]
            ipip = geolocation.ip_geolocation_ipip(ip)
            # if ipip["isp"] != "":
            #     continue
            # ipinfo = geolocation.ip_geolocation_ipinfo(ip)
            lng_ipip = float(ipip["longitude"])
            lat_ipip = float(ipip["latitude"])
            # lng_ipinfo = float(ipinfo["longitude"])
            # lat_ipinfo = float(ipinfo["latitude"])
            dis_max = 10000
            # dis0 = geolocation.geodistance(lng_ipip, lat_ipip, lng_ipinfo, lat_ipinfo)
            if ipip["isp"] == "":
                # print("dis0: %d, page: %s" % (dis0, json_pageinfo))
                coordi_by_page = get_coordination_by_page(json_pageinfo["html"], json_pageinfo["url"], ipip["city"])

                if coordi_by_page is not None:
                    dis1 = geolocation.geodistance(lng_ipip, lat_ipip, coordi_by_page["lng"], coordi_by_page["lat"])
                    # dis2 = geolocation.geodistance(lng_ipinfo, lat_ipinfo, coordi_by_page["lng"], coordi_by_page["lat"])
                    # print("dis1: %d, dis2: %d" % (dis1, dis2))
                    print("dis1: %s" % dis1)
                    # if dis1 < dis_max and dis2 < dis_max:
                    if dis1 < dis_max:
                        logger.war("dis: %s, page: %s" % (dis1, json_pageinfo))


    # landmarks = find_ip(landmarks)
    # json.dump(landmarks, open("../resources/landmarks_planetlab_0.1.json", "w"))


    # count = 0
    # for lm in landmarks:
    #     if lm["country"] == "United States":
    #         ipip = geolocation.ip_geolocation_ipip(lm["ip"])
    #         if ipip["isp"] not in settings.KEYWORD_CLOUD_PROVIDER:
    #             list_t, list_logo, list_cpy = [], [], []
    #
    #             if "html" in lm:
    #                 html = lm["html"]
    #                 url = lm["url"]
    #                 count += 1
    #                 query_str = oi.query_str(html, url)
    #                 lm["query_str"] = query_str
    #
    #                 logger.debug("ip: %s, url: %s, org: %s, query_str: %s" % (
    #                     lm["ip"], lm["url"], lm["organization"], query_str))
    #
    # print(count)
    # json.dump(landmarks, open("../resources/landmarks_planetlab_us.json", "w"))

    # landmarks = add_locinfo(landmarks)
    # json.dump(landmarks, open("../resources/landmarks_planetlab_0.3.json", "w"))
    # 0.2 geocoding
    # 0.3 ipinfo
    # 0.4 location
