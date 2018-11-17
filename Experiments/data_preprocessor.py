import requests
from Tools import requests_tools as rt, commercial_db,web_mapping_services
import re
from bs4 import BeautifulSoup
import socket
import pyprind


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
            json_ipinfo = commercial_db.ip_geolocation_ipinfo(ip)
            json_ipip = commercial_db.ip_geolocation_ipip(ip)
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
    '''
    use coordinate to locate ip to city-level by google map
    :param landmarks_planetlab:
    :return:
    '''
    for lm in pyprind.prog_bar(landmarks_planetlab):
        addr = web_mapping_services.google_map_geocode_coordinate2addr(float(lm["longitude"]), float(lm["latitude"]))
        if addr:
            lm["geo_lnglat"] = addr
    return landmarks_planetlab

