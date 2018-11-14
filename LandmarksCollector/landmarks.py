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


def get_all_lm():
    # [{"name": "73.158.231.225", "value": 50}, {"name": "70.191.3.24", "value": 50}, {"name": "24.94.19.39", "value": 50}, {"name": "173.72.219.183", "value": 50}, {"name": "24.11.37.175", "value": 50}, {"name": "76.176.109.35", "value": 50}, {"name": "73.95.181.204", "value": 50}, {"name": "169.228.128.3", "value": 50}, {"name": "192.159.10.223", "value": 50}, {"name": "67.180.9.146", "value": 50}, {"name": "72.50.192.24", "value": 50}, {"name": "73.239.252.114", "value": 50}, {"name": "141.213.135.222", "value": 50}, {"name": "199.212.124.181", "value": 50}, {"name": "76.183.147.45", "value": 50}, {"name": "76.116.155.46", "value": 50}, {"name": "96.231.108.118", "value": 50}, {"name": "70.90.143.154", "value": 50}, {"name": "149.20.4.9", "value": 50}, {"name": "75.33.221.50", "value": 50}, {"name": "72.225.214.9", "value": 50}, {"name": "50.35.71.192", "value": 50}, {"name": "142.196.242.41", "value": 50}, {"name": "73.251.80.221", "value": 50}, {"name": "50.93.222.130", "value": 50}, {"name": "128.8.126.180", "value": 50}, {"name": "108.20.171.62", "value": 50}, {"name": "68.45.52.117", "value": 50}, {"name": "66.31.202.23", "value": 50}, {"name": "73.169.119.159", "value": 50}, {"name": "71.96.207.242", "value": 50}, {"name": "204.2.211.147", "value": 50}, {"name": "24.16.172.3", "value": 50}, {"name": "162.195.241.81", "value": 50}, {"name": "65.190.196.16", "value": 50}, {"name": "73.149.148.225", "value": 50}, {"name": "192.0.35.210", "value": 50}, {"name": "73.225.5.190", "value": 50}, {"name": "75.74.255.171", "value": 50}, {"name": "204.9.55.84", "value": 50}, {"name": "24.49.62.214", "value": 50}, {"name": "204.9.221.254", "value": 50}, {"name": "71.62.75.209", "value": 50}, {"name": "153.16.25.235", "value": 50}, {"name": "73.96.132.59", "value": 50}, {"name": "99.22.6.116", "value": 50}, {"name": "73.133.106.37", "value": 50}, {"name": "98.195.89.90", "value": 50}, {"name": "216.67.35.146", "value": 50}, {"name": "209.6.43.168", "value": 50}, {"name": "192.94.214.98", "value": 50}, {"name": "76.122.69.118", "value": 50}, {"name": "50.0.7.110", "value": 50}, {"name": "68.33.69.55", "value": 50}, {"name": "75.101.48.145", "value": 50}, {"name": "24.21.130.235", "value": 50}, {"name": "162.228.246.62", "value": 50}, {"name": "71.58.99.157", "value": 50}, {"name": "68.78.72.17", "value": 50}, {"name": "67.168.234.202", "value": 50}, {"name": "67.180.86.248", "value": 50}, {"name": "72.83.51.107", "value": 50}, {"name": "73.202.177.209", "value": 50}, {"name": "96.255.43.79", "value": 50}, {"name": "104.148.234.128", "value": 50}, {"name": "96.231.151.201", "value": 50}, {"name": "108.16.47.140", "value": 50}, {"name": "173.76.170.27", "value": 50}, {"name": "174.130.119.169", "value": 50}, {"name": "24.14.13.56", "value": 50}, {"name": "98.207.188.66", "value": 50}, {"name": "50.244.229.105", "value": 50}, {"name": "75.140.57.34", "value": 50}, {"name": "73.227.233.90", "value": 50}, {"name": "76.14.101.62", "value": 50}, {"name": "216.66.102.83", "value": 50}, {"name": "104.162.110.2", "value": 50}, {"name": "50.89.10.170", "value": 50}, {"name": "108.49.142.204", "value": 50}, {"name": "47.14.34.192", "value": 50}, {"name": "50.37.95.236", "value": 50}, {"name": "23.24.51.6", "value": 50}, {"name": "71.56.79.56", "value": 50}, {"name": "198.180.150.39", "value": 50}, {"name": "198.180.152.19", "value": 50}, {"name": "99.150.228.34", "value": 50}, {"name": "147.28.0.132", "value": 50}, {"name": "149.20.4.10", "value": 50}, {"name": "129.250.50.30", "value": 50}, {"name": "129.250.50.34", "value": 50}, {"name": "129.250.50.37", "value": 50}, {"name": "129.250.50.42", "value": 50}, {"name": "199.7.183.254", "value": 50}, {"name": "76.26.115.194", "value": 50}, {"name": "198.199.99.218", "value": 50}, {"name": "76.26.120.98", "value": 50}, {"name": "208.80.155.69", "value": 50}, {"name": "208.80.152.244", "value": 50}, {"name": "198.35.26.244", "value": 50}, {"name": "209.59.185.7", "value": 50}, {"name": "50.28.98.185", "value": 50}, {"name": "192.0.33.157", "value": 50}, {"name": "192.0.46.157", "value": 50}, {"name": "199.115.158.230", "value": 50}, {"name": "185.28.222.65", "value": 50}, {"name": "65.22.12.230", "value": 50}, {"name": "108.59.15.3", "value": 50}, {"name": "209.58.135.163", "value": 50}, {"name": "134.197.113.7", "value": 50}, {"name": "74.118.183.198", "value": 50}, {"name": "164.113.94.217", "value": 50}, {"name": "185.114.152.90", "value": 50}, {"name": "128.112.128.33", "value": 50}, {"name": "192.172.226.235", "value": 50}, {"name": "204.8.154.50", "value": 50}, {"name": "199.201.65.212", "value": 50}, {"name": "128.173.192.58", "value": 50}, {"name": "74.208.134.54", "value": 50}, {"name": "68.232.38.39", "value": 50}, {"name": "152.195.92.35", "value": 50}, {"name": "68.232.39.54", "value": 50}, {"name": "204.15.11.34", "value": 50}, {"name": "163.237.247.18", "value": 50}, {"name": "72.21.93.35", "value": 50}, {"name": "68.232.37.34", "value": 50}, {"name": "69.89.207.87", "value": 50}, {"name": "192.229.156.101", "value": 50}, {"name": "68.232.36.46", "value": 50}, {"name": "46.22.79.34", "value": 50}, {"name": "152.195.28.20", "value": 50}, {"name": "192.136.136.221", "value": 50}, {"name": "204.42.254.42", "value": 50}, {"name": "34.202.174.53", "value": 50}, {"name": "69.30.249.206", "value": 50}, {"name": "104.225.3.74", "value": 50}, {"name": "208.40.192.202", "value": 50}, {"name": "208.86.250.253", "value": 50}, {"name": "107.162.223.5", "value": 50}, {"name": "104.225.102.122", "value": 50}, {"name": "104.225.15.170", "value": 50}, {"name": "107.162.217.5", "value": 50}, {"name": "71.202.134.1", "value": 50}, {"name": "73.158.231.225", "value": 50}, {"name": "73.207.22.128", "value": 50}, {"name": "76.167.217.81", "value": 50}, {"name": "75.150.193.178", "value": 50}, {"name": "157.131.74.98", "value": 50}, {"name": "68.45.52.117", "value": 50}, {"name": "72.50.192.24", "value": 50}, {"name": "38.103.166.4", "value": 50}, {"name": "204.11.230.180", "value": 50}, {"name": "45.36.19.9", "value": 50}, {"name": "192.136.193.180", "value": 50}, {"name": "73.4.218.247", "value": 50}, {"name": "76.28.152.19", "value": 50}, {"name": "77.250.231.27", "value": 50}, {"name": "73.217.95.41", "value": 50}, {"name": "144.121.16.186", "value": 50}, {"name": "23.28.75.227", "value": 50}, {"name": "74.87.143.38", "value": 50}, {"name": "24.180.57.87", "value": 50}, {"name": "76.123.25.45", "value": 50}, {"name": "71.200.48.207", "value": 50}, {"name": "216.186.200.129", "value": 50}, {"name": "192.122.200.170", "value": 50}, {"name": "69.2.47.30", "value": 50}, {"name": "71.127.254.53", "value": 50}, {"name": "76.117.16.125", "value": 50}, {"name": "68.48.102.241", "value": 50}, {"name": "72.201.9.19", "value": 50}, {"name": "141.151.27.126", "value": 50}, {"name": "174.63.182.146", "value": 50}, {"name": "74.104.169.123", "value": 50}, {"name": "128.114.139.114", "value": 50}, {"name": "69.21.226.205", "value": 50}, {"name": "204.246.3.62", "value": 50}, {"name": "192.33.255.26", "value": 50}, {"name": "64.73.41.116", "value": 50}, {"name": "100.7.255.235", "value": 50}, {"name": "67.82.50.43", "value": 50}, {"name": "70.20.54.178", "value": 50}, {"name": "204.111.162.136", "value": 50}, {"name": "68.110.8.86", "value": 50}, {"name": "185.148.180.11", "value": 50}, {"name": "174.55.34.149", "value": 50}, {"name": "71.126.171.160", "value": 50}, {"name": "76.186.174.22", "value": 50}, {"name": "73.249.28.7", "value": 50}, {"name": "24.14.246.171", "value": 50}, {"name": "64.121.248.150", "value": 50}, {"name": "50.202.87.154", "value": 50}, {"name": "24.16.203.93", "value": 50}, {"name": "76.124.124.97", "value": 50}, {"name": "76.165.193.133", "value": 50}, {"name": "67.242.152.252", "value": 50}, {"name": "63.130.83.21", "value": 50}, {"name": "63.130.83.29", "value": 50}, {"name": "65.34.213.184", "value": 50}, {"name": "174.53.136.164", "value": 50}, {"name": "73.44.59.213", "value": 50}, {"name": "99.100.86.150", "value": 50}, {"name": "67.174.3.44", "value": 50}, {"name": "73.74.200.91", "value": 50}, {"name": "69.245.130.70", "value": 50}, {"name": "174.60.106.14", "value": 50}, {"name": "67.186.153.148", "value": 50}, {"name": "24.247.146.249", "value": 50}, {"name": "23.240.241.44", "value": 50}, {"name": "98.110.161.218", "value": 50}, {"name": "98.160.100.130", "value": 50}, {"name": "73.6.150.62", "value": 50}, {"name": "76.124.130.88", "value": 50}, {"name": "73.128.129.77", "value": 50}, {"name": "174.49.169.194", "value": 50}, {"name": "107.77.229.235", "value": 50}, {"name": "24.218.80.205", "value": 50}, {"name": "73.52.71.160", "value": 50}, {"name": "67.228.81.214", "value": 50}, {"name": "50.23.39.62", "value": 50}, {"name": "206.197.161.186", "value": 50}, {"name": "50.23.93.62", "value": 50}, {"name": "173.192.213.14", "value": 50}, {"name": "50.23.207.118", "value": 50}, {"name": "76.104.3.65", "value": 50}, {"name": "73.17.97.243", "value": 50}, {"name": "108.51.128.74", "value": 50}, {"name": "76.208.83.249", "value": 50}, {"name": "73.221.140.93", "value": 50}, {"name": "73.129.151.141", "value": 50}, {"name": "108.41.29.197", "value": 50}, {"name": "198.108.63.99", "value": 50}, {"name": "71.234.74.27", "value": 50}, {"name": "207.182.40.10", "value": 50}, {"name": "151.201.145.230", "value": 50}, {"name": "130.111.39.128", "value": 50}, {"name": "108.208.27.175", "value": 50}, {"name": "12.0.1.55", "value": 50}, {"name": "172.10.12.5", "value": 50}, {"name": "192.136.136.246", "value": 50}, {"name": "74.192.7.62", "value": 50}, {"name": "73.150.238.226", "value": 50}, {"name": "96.76.225.45", "value": 50}, {"name": "204.2.134.10", "value": 50}, {"name": "98.29.129.251", "value": 50}, {"name": "47.152.38.212", "value": 50}, {"name": "45.19.223.97", "value": 50}, {"name": "96.241.66.134", "value": 50}, {"name": "71.231.59.21", "value": 50}, {"name": "209.33.220.90", "value": 50}, {"name": "71.8.135.104", "value": 50}, {"name": "24.18.250.21", "value": 50}, {"name": "204.139.52.240", "value": 50}, {"name": "136.56.105.144", "value": 50}, {"name": "76.211.117.43", "value": 50}, {"name": "172.92.1.230", "value": 50}, {"name": "68.37.21.198", "value": 50}, {"name": "193.37.253.107", "value": 50}, {"name": "76.124.24.216", "value": 50}, {"name": "73.158.39.122", "value": 50}, {"name": "69.142.87.206", "value": 50}, {"name": "73.123.179.209", "value": 50}, {"name": "24.17.77.25", "value": 50}, {"name": "98.214.101.171", "value": 50}, {"name": "71.56.103.128", "value": 50}, {"name": "68.98.96.203", "value": 50}, {"name": "50.107.9.235", "value": 50}, {"name": "174.18.150.26", "value": 50}, {"name": "108.222.120.191", "value": 50}, {"name": "72.79.10.243", "value": 50}, {"name": "47.151.137.110", "value": 50}, {"name": "75.111.77.103", "value": 50}, {"name": "174.77.43.177", "value": 50}, {"name": "73.7.146.24", "value": 50}, {"name": "108.195.89.236", "value": 50}, {"name": "173.29.59.254", "value": 50}, {"name": "72.21.67.50", "value": 50}, {"name": "24.101.225.24", "value": 50}, {"name": "73.110.200.155", "value": 50}, {"name": "69.139.117.97", "value": 50}, {"name": "209.249.60.243", "value": 50}, {"name": "50.1.51.141", "value": 50}, {"name": "173.71.95.143", "value": 50}, {"name": "50.117.26.108", "value": 50}, {"name": "47.20.133.70", "value": 50}, {"name": "146.115.214.171", "value": 50}, {"name": "12.156.204.230", "value": 50}, {"name": "45.17.13.240", "value": 50}, {"name": "70.131.33.76", "value": 50}, {"name": "69.255.157.207", "value": 50}, {"name": "98.11.6.2", "value": 50}, {"name": "12.18.223.58", "value": 50}, {"name": "173.81.78.192", "value": 50}, {"name": "172.79.68.167", "value": 50}, {"name": "64.121.83.6", "value": 50}, {"name": "64.79.54.240", "value": 50}, {"name": "98.21.244.213", "value": 50}, {"name": "192.148.252.30", "value": 50}, {"name": "76.117.240.28", "value": 50}, {"name": "173.243.177.185", "value": 50}, {"name": "24.238.41.216", "value": 50}, {"name": "134.84.88.118", "value": 50}, {"name": "67.169.33.196", "value": 50}, {"name": "173.228.90.186", "value": 50}, {"name": "198.244.105.107", "value": 50}, {"name": "67.180.172.13", "value": 50}, {"name": "73.225.61.239", "value": 50}, {"name": "73.89.156.84", "value": 50}, {"name": "73.35.163.21", "value": 50}, {"name": "73.201.248.91", "value": 50}, {"name": "73.189.102.43", "value": 50}, {"name": "73.180.237.180", "value": 50}, {"name": "97.113.109.228", "value": 50}, {"name": "174.48.146.205", "value": 50}, {"name": "73.159.137.68", "value": 50}, {"name": "73.8.76.8", "value": 50}, {"name": "174.105.206.164", "value": 50}, {"name": "75.135.177.24", "value": 50}, {"name": "50.0.69.63", "value": 50}, {"name": "173.80.116.127", "value": 50}, {"name": "24.6.172.77", "value": 50}, {"name": "68.175.130.230", "value": 50}, {"name": "47.189.38.249", "value": 50}, {"name": "198.27.221.1", "value": 50}, {"name": "97.82.209.17", "value": 50}, {"name": "73.217.8.61", "value": 50}, {"name": "69.11.182.222", "value": 50}, {"name": "73.186.137.119", "value": 50}, {"name": "67.169.138.35", "value": 50}, {"name": "173.167.0.106", "value": 50}, {"name": "157.131.93.203", "value": 50}, {"name": "73.189.60.147", "value": 50}, {"name": "162.217.72.122", "value": 50}, {"name": "108.20.245.238", "value": 50}, {"name": "70.88.254.62", "value": 50}, {"name": "173.66.193.119", "value": 50}, {"name": "98.225.183.175", "value": 50}, {"name": "24.147.4.232", "value": 50}, {"name": "98.248.50.174", "value": 50}, {"name": "73.202.185.104", "value": 50}, {"name": "73.157.224.176", "value": 50}, {"name": "73.189.248.203", "value": 50}, {"name": "96.241.220.148", "value": 50}, {"name": "73.252.177.33", "value": 50}, {"name": "107.129.70.7", "value": 50}, {"name": "12.12.144.130", "value": 50}, {"name": "65.175.133.136", "value": 50}, {"name": "38.103.8.29", "value": 50}, {"name": "50.225.148.86", "value": 50}, {"name": "64.251.60.30", "value": 50}, {"name": "69.119.129.128", "value": 50}, {"name": "174.69.138.222", "value": 50}, {"name": "65.27.247.71", "value": 50}, {"name": "70.91.226.205", "value": 50}, {"name": "208.82.98.77", "value": 50}, {"name": "198.128.52.20", "value": 50}, {"name": "45.26.126.41", "value": 50}, {"name": "99.34.233.149", "value": 50}, {"name": "107.3.72.5", "value": 50}, {"name": "73.255.72.5", "value": 50}, {"name": "67.160.162.178", "value": 50}, {"name": "99.124.138.140", "value": 50}, {"name": "73.134.145.57", "value": 50}, {"name": "71.120.0.157", "value": 50}, {"name": "68.81.67.173", "value": 50}, {"name": "128.118.46.199", "value": 50}, {"name": "73.93.124.102", "value": 50}, {"name": "99.52.253.161", "value": 50}, {"name": "72.76.184.201", "value": 50}, {"name": "18.26.2.101", "value": 50}, {"name": "69.47.91.34", "value": 50}, {"name": "47.203.191.118", "value": 50}, {"name": "98.29.126.243", "value": 50}, {"name": "50.126.112.105", "value": 50}, {"name": "198.207.145.170", "value": 50}, {"name": "76.219.105.160", "value": 50}, {"name": "131.93.241.21", "value": 50}, {"name": "66.119.109.100", "value": 50}, {"name": "108.166.188.148", "value": 50}, {"name": "98.24.59.17", "value": 50}, {"name": "73.254.74.61", "value": 50}, {"name": "73.193.14.143", "value": 50}, {"name": "24.19.93.19", "value": 50}, {"name": "71.84.13.72", "value": 50}, {"name": "173.164.200.74", "value": 50}, {"name": "73.243.44.225", "value": 50}, {"name": "67.183.118.241", "value": 50}, {"name": "71.50.18.48", "value": 50}, {"name": "68.47.116.75", "value": 50}, {"name": "71.198.119.116", "value": 50}, {"name": "206.167.70.238", "value": 50}, {"name": "65.50.210.58", "value": 50}, {"name": "67.169.45.178", "value": 50}, {"name": "204.111.160.136", "value": 50}, {"name": "66.91.16.75", "value": 50}, {"name": "128.171.6.63", "value": 50}, {"name": "73.38.119.151", "value": 50}, {"name": "73.54.62.64", "value": 50}, {"name": "66.30.9.161", "value": 50}, {"name": "68.197.125.86", "value": 50}, {"name": "24.15.0.4", "value": 50}, {"name": "73.96.94.113", "value": 50}, {"name": "130.245.145.107", "value": 50}, {"name": "130.245.145.108", "value": 50}, {"name": "199.255.191.82", "value": 50}, {"name": "45.37.215.93", "value": 50}, {"name": "75.72.254.63", "value": 50}, {"name": "173.79.42.13", "value": 50}, {"name": "174.81.245.186", "value": 50}, {"name": "73.180.4.136", "value": 50}, {"name": "73.190.89.6", "value": 50}, {"name": "173.77.170.228", "value": 50}, {"name": "70.113.73.127", "value": 50}, {"name": "24.4.33.236", "value": 50}, {"name": "72.177.90.195", "value": 50}, {"name": "69.201.42.185", "value": 50}, {"name": "24.220.254.130", "value": 50}, {"name": "50.122.236.212", "value": 50}, {"name": "173.89.28.154", "value": 50}, {"name": "47.156.128.231", "value": 50}, {"name": "129.10.110.12", "value": 50}, {"name": "169.232.255.61", "value": 50}, {"name": "75.142.226.232", "value": 50}, {"name": "172.91.212.133", "value": 50}, {"name": "74.115.180.218", "value": 50}, {"name": "108.56.138.112", "value": 50}, {"name": "160.2.150.254", "value": 50}, {"name": "200.40.66.197", "value": 50}, {"name": "73.15.21.3", "value": 50}, {"name": "206.221.144.118", "value": 50}, {"name": "76.24.182.116", "value": 50}, {"name": "66.91.17.183", "value": 50}, {"name": "184.16.192.112", "value": 50}, {"name": "72.253.155.91", "value": 50}, {"name": "96.95.123.217", "value": 50}, {"name": "100.35.124.65", "value": 50}, {"name": "97.113.61.249", "value": 50}, {"name": "184.96.160.96", "value": 50}, {"name": "99.23.121.193", "value": 50}, {"name": "24.6.34.24", "value": 50}, {"name": "157.131.155.226", "value": 50}, {"name": "184.100.5.95", "value": 50}, {"name": "132.147.59.214", "value": 50}, {"name": "70.174.128.28", "value": 50}, {"name": "98.228.226.198", "value": 50}, {"name": "76.169.161.134", "value": 50}, {"name": "73.71.83.186", "value": 50}, {"name": "170.72.9.235", "value": 50}, {"name": "75.163.222.146", "value": 50}, {"name": "98.118.40.116", "value": 50}, {"name": "173.73.115.58", "value": 50}, {"name": "208.87.223.18", "value": 50}, {"name": "69.250.46.25", "value": 50}, {"name": "73.60.220.71", "value": 50}, {"name": "71.197.3.75", "value": 50}, {"name": "66.235.10.92", "value": 50}, {"name": "207.72.6.200", "value": 50}, {"name": "68.38.144.8", "value": 50}, {"name": "217.10.140.66", "value": 50}, {"name": "73.232.114.226", "value": 50}, {"name": "76.236.29.168", "value": 50}, {"name": "66.180.193.221", "value": 50}, {"name": "71.244.45.11", "value": 50}, {"name": "73.52.80.84", "value": 50}, {"name": "97.115.127.231", "value": 50}, {"name": "69.117.162.131", "value": 50}, {"name": "67.180.62.33", "value": 50}, {"name": "12.131.8.218", "value": 50}, {"name": "73.92.164.144", "value": 50}, {"name": "73.217.82.19", "value": 50}, {"name": "24.148.31.23", "value": 50}, {"name": "70.123.105.101", "value": 50}, {"name": "75.142.22.153", "value": 50}, {"name": "24.218.77.29", "value": 50}, {"name": "173.76.130.77", "value": 50}, {"name": "107.130.64.185", "value": 50}, {"name": "73.15.72.77", "value": 50}, {"name": "44.98.248.130", "value": 50}, {"name": "70.121.97.7", "value": 50}, {"name": "208.108.195.238", "value": 50}, {"name": "128.3.125.92", "value": 50}, {"name": "204.210.109.71", "value": 50}, {"name": "128.138.75.184", "value": 50}, {"name": "73.249.228.154", "value": 50}, {"name": "76.179.53.236", "value": 50}, {"name": "65.254.97.105", "value": 50}, {"name": "129.21.208.111", "value": 50}, {"name": "71.121.144.214", "value": 50}, {"name": "108.58.6.98", "value": 50}, {"name": "71.211.157.247", "value": 50}, {"name": "50.126.247.194", "value": 50}, {"name": "98.155.35.172", "value": 50}, {"name": "65.182.164.62", "value": 50}, {"name": "47.149.129.143", "value": 50}, {"name": "104.225.112.30", "value": 50}, {"name": "50.43.44.26", "value": 50}, {"name": "104.238.192.2", "value": 50}, {"name": "50.0.94.17", "value": 50}, {"name": "50.246.243.53", "value": 50}, {"name": "73.92.214.30", "value": 50}, {"name": "157.131.93.37", "value": 50}, {"name": "136.24.13.23", "value": 50}, {"name": "73.110.148.138", "value": 50}, {"name": "157.131.196.97", "value": 50}, {"name": "23.130.129.98", "value": 50}, {"name": "146.115.129.98", "value": 50}, {"name": "98.172.94.4", "value": 50}, {"name": "162.213.60.7", "value": 50}, {"name": "73.252.184.74", "value": 50}, {"name": "107.15.168.195", "value": 50}, {"name": "144.202.128.5", "value": 50}, {"name": "107.15.168.195", "value": 50}, {"name": "108.217.53.158", "value": 50}, {"name": "204.13.164.13", "value": 50}, {"name": "216.243.57.193", "value": 50}, {"name": "76.218.237.4", "value": 50}, {"name": "73.192.209.248", "value": 50}, {"name": "97.117.66.192", "value": 50}, {"name": "73.253.63.209", "value": 50}, {"name": "198.137.202.120", "value": 50}, {"name": "184.177.189.254", "value": 50}, {"name": "73.109.215.184", "value": 50}, {"name": "47.14.40.177", "value": 50}, {"name": "140.88.102.20", "value": 50}, {"name": "73.94.72.190", "value": 50}, {"name": "207.229.130.137", "value": 50}, {"name": "173.228.88.84", "value": 50}, {"name": "96.230.244.101", "value": 50}, {"name": "72.79.242.5", "value": 50}, {"name": "71.198.26.115", "value": 50}, {"name": "184.166.173.192", "value": 50}, {"name": "99.124.138.140", "value": 50}, {"name": "99.27.141.31", "value": 50}, {"name": "73.159.158.36", "value": 50}, {"name": "166.70.73.161", "value": 50}, {"name": "71.90.87.66", "value": 50}, {"name": "50.252.93.92", "value": 50}, {"name": "129.19.47.14", "value": 50}, {"name": "128.105.22.238", "value": 50}, {"name": "50.53.18.99", "value": 50}, {"name": "108.226.113.200", "value": 50}, {"name": "66.177.255.113", "value": 50}, {"name": "73.116.127.174", "value": 50}, {"name": "73.40.33.2", "value": 50}, {"name": "74.78.75.254", "value": 50}, {"name": "75.108.88.191", "value": 50}, {"name": "74.73.116.91", "value": 50}, {"name": "68.55.30.51", "value": 50}, {"name": "98.211.64.149", "value": 50}, {"name": "71.187.192.8", "value": 50}, {"name": "47.23.69.66", "value": 50}, {"name": "23.116.215.225", "value": 50}, {"name": "173.228.7.217", "value": 50}, {"name": "64.136.224.8", "value": 50}, {"name": "69.146.25.47", "value": 50}, {"name": "38.66.197.240", "value": 50}, {"name": "50.200.146.222", "value": 50}, {"name": "72.93.214.153", "value": 50}, {"name": "100.38.237.108", "value": 50}, {"name": "66.35.1.50", "value": 50}, {"name": "67.5.109.37", "value": 50}, {"name": "97.113.96.67", "value": 50}, {"name": "98.210.241.163", "value": 50}, {"name": "50.204.69.193", "value": 50}, {"name": "98.127.186.150", "value": 50}, {"name": "173.49.196.136", "value": 50}, {"name": "67.161.26.24", "value": 50}, {"name": "69.138.163.241", "value": 50}, {"name": "64.222.183.214", "value": 50}, {"name": "71.195.31.218", "value": 50}, {"name": "173.76.33.19", "value": 50}, {"name": "75.71.196.231", "value": 50}, {"name": "98.163.10.98", "value": 50}, {"name": "76.124.81.185", "value": 50}, {"name": "216.56.3.74", "value": 50}, {"name": "216.243.32.70", "value": 50}, {"name": "73.2.43.237", "value": 50}, {"name": "173.241.172.221", "value": 50}, {"name": "67.160.239.209", "value": 50}, {"name": "107.167.193.118", "value": 50}, {"name": "76.188.48.74", "value": 50}, {"name": "71.196.154.60", "value": 50}, {"name": "73.122.220.24", "value": 50}, {"name": "162.231.243.83", "value": 50}, {"name": "68.100.248.189", "value": 50}, {"name": "73.14.190.183", "value": 50}, {"name": "68.115.154.254", "value": 50}, {"name": "128.171.47.239", "value": 50}, {"name": "207.136.192.158", "value": 50}, {"name": "47.158.138.13", "value": 50}, {"name": "172.74.51.181", "value": 50}, {"name": "76.91.3.33", "value": 50}, {"name": "208.70.144.17", "value": 50}, {"name": "130.85.61.5", "value": 50}, {"name": "216.176.178.18", "value": 50}, {"name": "47.144.144.180", "value": 50}, {"name": "71.192.65.151", "value": 50}, {"name": "70.93.153.68", "value": 50}, {"name": "100.19.12.61", "value": 50}, {"name": "73.159.137.214", "value": 50}, {"name": "73.53.65.241", "value": 50}, {"name": "66.169.246.33", "value": 50}, {"name": "71.127.158.50", "value": 50}, {"name": "70.57.20.78", "value": 50}, {"name": "67.174.213.204", "value": 50}, {"name": "69.181.5.13", "value": 50}, {"name": "71.198.13.164", "value": 50}, {"name": "71.51.174.155", "value": 50}, {"name": "99.137.191.34", "value": 50}, {"name": "68.107.118.40", "value": 50}, {"name": "166.130.104.242", "value": 50}, {"name": "73.139.164.57", "value": 50}, {"name": "73.245.251.173", "value": 50}, {"name": "71.225.156.34", "value": 50}, {"name": "47.196.158.32", "value": 50}, {"name": "74.88.76.96", "value": 50}, {"name": "50.246.66.190", "value": 50}, {"name": "128.118.46.198", "value": 50}, {"name": "65.254.97.49", "value": 50}, {"name": "65.254.97.52", "value": 50}, {"name": "135.84.58.40", "value": 50}, {"name": "65.254.97.40", "value": 50}, {"name": "135.84.56.40", "value": 50}, {"name": "65.254.97.43", "value": 50}, {"name": "70.167.13.75", "value": 50}, {"name": "135.84.56.43", "value": 50}, {"name": "174.67.25.77", "value": 50}, {"name": "174.62.70.109", "value": 50}, {"name": "96.255.61.139", "value": 50}, {"name": "174.25.169.168", "value": 50}, {"name": "50.109.227.231", "value": 50}, {"name": "67.197.25.215", "value": 50}, {"name": "96.81.32.158", "value": 50}, {"name": "67.161.160.12", "value": 50}, {"name": "174.69.133.241", "value": 50}, {"name": "73.181.98.53", "value": 50}, {"name": "100.2.36.112", "value": 50}, {"name": "69.71.0.45", "value": 50}, {"name": "136.32.6.174", "value": 50}, {"name": "140.186.85.205", "value": 50}, {"name": "71.206.75.171", "value": 50}, {"name": "24.225.122.35", "value": 50}, {"name": "66.79.142.10", "value": 50}, {"name": "104.61.88.81", "value": 50}, {"name": "130.245.145.149", "value": 50}, {"name": "136.63.76.184", "value": 50}, {"name": "68.96.186.77", "value": 50}, {"name": "50.103.121.78", "value": 50}, {"name": "162.255.8.150", "value": 50}, {"name": "128.9.160.61", "value": 50}, {"name": "192.5.203.212", "value": 50}, {"name": "209.240.65.188", "value": 50}, {"name": "47.188.184.134", "value": 50}, {"name": "76.191.19.33", "value": 50}, {"name": "73.225.157.93", "value": 50}, {"name": "68.38.12.91", "value": 50}, {"name": "73.231.203.30", "value": 50}, {"name": "98.180.230.141", "value": 50}, {"name": "76.167.189.224", "value": 50}, {"name": "146.115.6.2", "value": 50}, {"name": "66.67.19.199", "value": 50}, {"name": "76.169.181.211", "value": 50}, {"name": "67.186.229.62", "value": 50}, {"name": "66.7.126.161", "value": 50}, {"name": "75.162.6.111", "value": 50}, {"name": "69.255.121.239", "value": 50}, {"name": "70.106.197.175", "value": 50}, {"name": "71.220.234.28", "value": 50}, {"name": "66.24.222.60", "value": 50}, {"name": "73.93.187.127", "value": 50}, {"name": "68.111.13.62", "value": 50}, {"name": "73.76.171.227", "value": 50}, {"name": "108.207.255.214", "value": 50}, {"name": "173.18.148.199", "value": 50}, {"name": "68.110.21.244", "value": 50}, {"name": "73.189.64.139", "value": 50}, {"name": "97.127.69.46", "value": 50}, {"name": "98.167.136.44", "value": 50}, {"name": "72.68.115.57", "value": 50}, {"name": "140.180.226.107", "value": 50}, {"name": "107.3.175.60", "value": 50}, {"name": "76.174.17.39", "value": 50}, {"name": "74.71.209.196", "value": 50}, {"name": "24.255.23.59", "value": 50}, {"name": "71.0.93.2", "value": 50}, {"name": "67.76.163.196", "value": 50}, {"name": "173.61.187.251", "value": 50}, {"name": "174.53.2.217", "value": 50}, {"name": "24.61.110.238", "value": 50}, {"name": "174.53.156.145", "value": 50}, {"name": "75.68.27.72", "value": 50}, {"name": "50.245.46.133", "value": 50}, {"name": "71.72.140.236", "value": 50}, {"name": "44.16.51.1", "value": 50}, {"name": "24.19.247.74", "value": 50}, {"name": "73.162.195.248", "value": 50}, {"name": "73.39.231.59", "value": 50}, {"name": "162.233.201.149", "value": 50}, {"name": "208.115.148.220", "value": 50}, {"name": "24.165.80.18", "value": 50}, {"name": "24.18.164.4", "value": 50}, {"name": "24.92.134.225", "value": 50}, {"name": "73.230.180.235", "value": 50}, {"name": "68.64.82.4", "value": 50}, {"name": "67.183.153.88", "value": 50}, {"name": "76.25.43.163", "value": 50}, {"name": "96.241.125.168", "value": 50}, {"name": "71.171.106.132", "value": 50}, {"name": "67.169.97.196", "value": 50}, {"name": "66.218.0.5", "value": 50}, {"name": "96.255.112.234", "value": 50}, {"name": "173.73.212.195", "value": 50}, {"name": "73.92.124.43", "value": 50}, {"name": "192.110.255.62", "value": 50}, {"name": "192.5.44.70", "value": 50}, {"name": "24.12.156.156", "value": 50}, {"name": "44.44.117.16", "value": 50}, {"name": "45.24.251.23", "value": 50}, {"name": "67.188.19.174", "value": 50}, {"name": "73.158.247.136", "value": 50}, {"name": "24.51.135.52", "value": 50}, {"name": "24.130.60.11", "value": 50}, {"name": "98.249.35.131", "value": 50}, {"name": "97.126.102.103", "value": 50}, {"name": "74.96.104.11", "value": 50}, {"name": "131.247.18.33", "value": 50}, {"name": "108.30.122.254", "value": 50}, {"name": "24.5.245.225", "value": 50}, {"name": "173.76.164.158", "value": 50}, {"name": "160.36.59.129", "value": 50}, {"name": "162.249.156.18", "value": 50}, {"name": "24.6.137.5", "value": 50}, {"name": "205.234.117.2", "value": 50}, {"name": "173.228.71.184", "value": 50}, {"name": "68.173.138.153", "value": 50}, {"name": "67.245.43.27", "value": 50}, {"name": "174.74.11.89", "value": 50}, {"name": "96.89.109.201", "value": 50}, {"name": "73.231.85.80", "value": 50}, {"name": "66.220.251.95", "value": 50}, {"name": "24.130.91.245", "value": 50}, {"name": "99.16.97.208", "value": 50}, {"name": "73.40.22.143", "value": 50}, {"name": "199.201.145.28", "value": 50}, {"name": "108.51.180.14", "value": 50}, {"name": "24.251.93.186", "value": 50}, {"name": "45.46.88.158", "value": 50}, {"name": "47.14.114.146", "value": 50}, {"name": "70.161.141.62", "value": 50}, {"name": "98.182.31.36", "value": 50}, {"name": "172.222.171.15", "value": 50}, {"name": "24.209.55.62", "value": 50}, {"name": "64.180.81.188", "value": 50}, {"name": "100.36.45.114", "value": 50}, {"name": "185.45.146.238", "value": 50}, {"name": "100.2.46.25", "value": 50}, {"name": "64.83.178.147", "value": 50}, {"name": "68.203.175.104", "value": 50}, {"name": "38.142.218.114", "value": 50}, {"name": "69.84.9.250", "value": 50}, {"name": "50.241.59.243", "value": 50}, {"name": "47.144.228.196", "value": 50}, {"name": "128.9.161.173", "value": 50}, {"name": "157.131.222.124", "value": 50}, {"name": "100.36.149.46", "value": 50}, {"name": "50.202.194.198", "value": 50}, {"name": "208.125.171.126", "value": 50}, {"name": "24.162.242.246", "value": 50}, {"name": "24.6.241.33", "value": 50}, {"name": "199.120.117.103", "value": 50}, {"name": "75.139.7.163", "value": 50}, {"name": "67.86.129.212", "value": 50}, {"name": "173.49.232.6", "value": 50}, {"name": "74.140.100.139", "value": 50}, {"name": "149.43.80.25", "value": 50}, {"name": "173.91.44.117", "value": 50}, {"name": "98.171.172.74", "value": 50}, {"name": "75.68.186.4", "value": 50}, {"name": "71.213.121.47", "value": 50}, {"name": "138.128.190.246", "value": 50}, {"name": "208.74.138.130", "value": 50}, {"name": "99.85.29.171", "value": 50}, {"name": "67.246.132.67", "value": 50}, {"name": "73.172.80.175", "value": 50}, {"name": "172.93.216.242", "value": 50}, {"name": "73.72.118.124", "value": 50}, {"name": "174.74.36.122", "value": 50}, {"name": "71.179.9.130", "value": 50}, {"name": "69.116.165.66", "value": 50}, {"name": "140.192.218.186", "value": 50}, {"name": "104.175.188.233", "value": 50}, {"name": "67.166.28.74", "value": 50}, {"name": "73.34.49.85", "value": 50}, {"name": "100.4.192.237", "value": 50}, {"name": "69.49.161.92", "value": 50}, {"name": "151.161.36.135", "value": 50}, {"name": "72.69.158.16", "value": 50}, {"name": "174.56.111.37", "value": 50}, {"name": "148.59.200.131", "value": 50}, {"name": "98.249.18.56", "value": 50}, {"name": "4.14.254.153", "value": 50}, {"name": "204.77.234.46", "value": 50}, {"name": "108.26.148.190", "value": 50}, {"name": "174.83.130.41", "value": 50}, {"name": "108.6.195.165", "value": 50}, {"name": "71.237.92.38", "value": 50}, {"name": "128.114.255.9", "value": 50}, {"name": "136.62.62.88", "value": 50}, {"name": "71.205.5.58", "value": 50}, {"name": "72.200.128.29", "value": 50}, {"name": "73.93.135.95", "value": 50}, {"name": "68.188.189.115", "value": 50}, {"name": "174.126.74.4", "value": 50}, {"name": "72.46.56.101", "value": 50}, {"name": "73.16.26.19", "value": 50}, {"name": "146.115.226.85", "value": 50}, {"name": "65.96.33.75", "value": 50}, {"name": "71.212.2.79", "value": 50}, {"name": "174.104.143.151", "value": 50}, {"name": "128.187.82.226", "value": 50}, {"name": "18.26.5.198", "value": 50}, {"name": "71.58.236.16", "value": 50}, {"name": "108.53.180.242", "value": 50}, {"name": "73.164.193.104", "value": 50}, {"name": "70.231.19.155", "value": 50}, {"name": "69.40.119.112", "value": 50}, {"name": "100.36.112.123", "value": 50}, {"name": "128.138.200.58", "value": 50}, {"name": "128.210.109.92", "value": 50}, {"name": "23.79.231.14", "value": 50}, {"name": "68.47.91.180", "value": 50}, {"name": "24.149.120.220", "value": 50}, {"name": "72.68.108.199", "value": 50}, {"name": "23.251.82.28", "value": 50}, {"name": "192.58.193.254", "value": 50}, {"name": "100.36.45.114", "value": 50}, {"name": "98.244.76.91", "value": 50}, {"name": "184.170.76.26", "value": 50}, {"name": "73.60.202.39", "value": 50}, {"name": "98.217.220.104", "value": 50}, {"name": "71.105.243.227", "value": 50}, {"name": "216.56.243.250", "value": 50}, {"name": "73.3.227.235", "value": 50}, {"name": "75.60.243.198", "value": 50}, {"name": "199.253.27.64", "value": 50}, {"name": "67.169.145.66", "value": 50}, {"name": "68.203.21.32", "value": 50}, {"name": "103.105.49.13", "value": 50}, {"name": "73.118.179.178", "value": 50}, {"name": "97.126.12.59", "value": 50}, {"name": "73.69.249.75", "value": 50}, {"name": "104.58.80.93", "value": 50}, {"name": "73.169.57.109", "value": 50}, {"name": "147.92.96.57", "value": 50}, {"name": "208.90.212.227", "value": 50}, {"name": "173.24.67.141", "value": 50}, {"name": "172.91.77.0", "value": 50}, {"name": "96.32.152.183", "value": 50}, {"name": "108.44.215.199", "value": 50}, {"name": "205.234.237.186", "value": 50}, {"name": "73.54.189.183", "value": 50}, {"name": "128.119.150.41", "value": 50}, {"name": "71.146.225.254", "value": 50}, {"name": "66.68.32.163", "value": 50}, {"name": "47.38.143.240", "value": 50}, {"name": "69.31.144.4", "value": 50}, {"name": "50.83.106.180", "value": 50}, {"name": "67.52.187.132", "value": 50}, {"name": "71.142.7.89", "value": 50}, {"name": "99.126.115.47", "value": 50}, {"name": "98.214.242.200", "value": 50}, {"name": "96.35.114.157", "value": 50}, {"name": "67.41.198.253", "value": 50}, {"name": "108.189.28.77", "value": 50}, {"name": "24.60.164.179", "value": 50}, {"name": "75.139.128.41", "value": 50}, {"name": "98.195.254.112", "value": 50}, {"name": "44.94.64.2", "value": 50}, {"name": "68.83.168.2", "value": 50}, {"name": "45.26.150.95", "value": 50}, {"name": "24.213.105.50", "value": 50}, {"name": "24.208.48.88", "value": 50}, {"name": "47.210.79.154", "value": 50}, {"name": "50.24.106.182", "value": 50}, {"name": "198.90.14.26", "value": 50}, {"name": "108.39.67.39", "value": 50}, {"name": "44.4.17.147", "value": 50}, {"name": "73.11.174.19", "value": 50}, {"name": "24.42.211.232", "value": 50}, {"name": "74.192.110.215", "value": 50}, {"name": "104.175.197.189", "value": 50}, {"name": "98.191.114.228", "value": 50}, {"name": "76.30.9.35", "value": 50}, {"name": "70.162.239.240", "value": 50}, {"name": "73.169.7.152", "value": 50}, {"name": "73.231.222.217", "value": 50}, {"name": "24.17.245.235", "value": 50}, {"name": "100.36.2.228", "value": 50}, {"name": "173.217.67.169", "value": 50}, {"name": "184.0.77.78", "value": 50}, {"name": "139.138.66.149", "value": 50}, {"name": "174.100.201.24", "value": 50}, {"name": "45.17.162.192", "value": 50}, {"name": "47.149.95.49", "value": 50}, {"name": "172.90.248.45", "value": 50}, {"name": "98.115.150.55", "value": 50}, {"name": "100.14.130.194", "value": 50}, {"name": "98.249.124.21", "value": 50}, {"name": "199.184.246.170", "value": 50}, {"name": "67.149.228.19", "value": 50}, {"name": "74.64.100.120", "value": 50}, {"name": "72.223.40.102", "value": 50}, {"name": "71.90.95.111", "value": 50}, {"name": "73.93.161.145", "value": 50}, {"name": "24.213.124.190", "value": 50}, {"name": "71.143.145.144", "value": 50}, {"name": "72.175.44.196", "value": 50}, {"name": "64.234.27.94", "value": 50}, {"name": "97.99.108.155", "value": 50}, {"name": "108.53.170.206", "value": 50}, {"name": "76.193.120.181", "value": 50}, {"name": "108.14.72.48", "value": 50}, {"name": "71.62.65.192", "value": 50}, {"name": "73.176.137.8", "value": 50}, {"name": "217.28.163.28", "value": 50}, {"name": "204.110.191.190", "value": 50}, {"name": "198.105.231.114", "value": 50}, {"name": "129.244.208.56", "value": 50}, {"name": "104.185.207.122", "value": 50}, {"name": "209.180.211.163", "value": 50}, {"name": "47.35.37.159", "value": 50}, {"name": "104.12.251.1", "value": 50}, {"name": "38.107.148.196", "value": 50}, {"name": "65.60.173.98", "value": 50}, {"name": "71.172.152.130", "value": 50}, {"name": "75.111.238.244", "value": 50}, {"name": "107.210.94.68", "value": 50}, {"name": "66.44.23.245", "value": 50}, {"name": "73.74.204.32", "value": 50}, {"name": "66.84.81.55", "value": 50}, {"name": "76.14.34.20", "value": 50}, {"name": "136.53.6.97", "value": 50}, {"name": "107.2.254.108", "value": 50}]

    # {"73.158.231.225": [-122.2725, 37.5115], "70.191.3.24": [-115.0215, 35.9515], "24.94.19.39": [-117.1815, 32.8885], "173.72.219.183": [-77.7395, 38.9695], "24.11.37.175": [-111.8785, 40.7805], "76.176.109.35": [-117.1615, 32.7195], "73.95.181.204": [-105.0925, 39.7985], "169.228.128.3": [-117.2315, 32.8775], "192.159.10.223": [-121.8105, 37.3095], "67.180.9.146": [-122.1585, 37.4575], "72.50.192.24": [-93.2725, 44.9775], "73.239.252.114": [-122.5705, 47.6615], "141.213.135.222": [-83.7425, 42.2795], "199.212.124.181": [-77.0525, 38.7985], "76.183.147.45": [-96.6415, 32.9075], "76.116.155.46": [-74.4315, 39.4885], "96.231.108.118": [-76.8515, 39.1005], "70.90.143.154": [-83.8515, 42.2675], "149.20.4.9": [-122.1415, 37.4385], "75.33.221.50": [-80.3615, 25.6685], "72.225.214.9": [-73.9515, 40.8095], "50.35.71.192": [-122.1215, 47.6705], "142.196.242.41": [-81.1205, 28.7415], "73.251.80.221": [-77.5195, 38.9875], "50.93.222.130": [-89.3895, 43.0685], "128.8.126.180": [-76.9395, 38.9915], "108.20.171.62": [-71.2295, 42.2315], "68.45.52.117": [-87.1685, 39.0305], "66.31.202.23": [-71.1185, 42.3795], "73.169.119.159": [-105.0285, 39.5795], "71.96.207.242": [-96.6785, 33.0315], "204.2.211.147": [-77.3625, 38.9515], "24.16.172.3": [-122.5685, 47.6095], "162.195.241.81": [-121.8885, 37.3115], "65.190.196.16": [-77.0215, 34.6705], "73.149.148.225": [-71.4215, 42.2815], "192.0.35.210": [-118.3885, 33.9275], "73.225.5.190": [-122.3285, 47.6085], "75.74.255.171": [-80.3285, 25.7795], "204.9.55.84": [-87.9705, 42.0015], "24.49.62.214": [-77.7025, 39.6585], "204.9.221.254": [-71.0825, 42.3615], "71.62.75.209": [-77.5025, 38.9675], "153.16.25.235": [-84.0815, 40.7985], "73.96.132.59": [-123.0515, 44.0395], "99.22.6.116": [-82.8815, 40.0195], "73.133.106.37": [-76.9495, 39.3995], "98.195.89.90": [-95.3695, 29.7615], "216.67.35.146": [-147.1185, 64.8615], "209.6.43.168": [-71.1025, 42.3875], "192.94.214.98": [-76.8605, 39.1975], "76.122.69.118": [-84.2205, 33.8495], "50.0.7.110": [-121.7505, 38.5695], "68.33.69.55": [-77.0505, 38.9215], "75.101.48.145": [-122.2905, 37.8675], "24.21.130.235": [-122.6805, 45.5205], "162.228.246.62": [-84.2995, 33.8875], "71.58.99.157": [-77.8595, 40.7905], "68.78.72.17": [-121.6995, 38.5575], "67.168.234.202": [-122.6095, 45.5075], "67.180.86.248": [-122.0595, 37.3885], "72.83.51.107": [-77.0885, 38.8785], "73.202.177.209": [-122.0785, 37.3895], "96.255.43.79": [-77.1625, 38.9795], "104.148.234.128": [-74.0115, 40.7795], "96.231.151.201": [-77.3715, 39.0405], "108.16.47.140": [-75.5205, 40.1105], "173.76.170.27": [-71.5695, 42.6105], "174.130.119.169": [-79.3295, 40.8215], "24.14.13.56": [-87.9885, 42.2695], "98.207.188.66": [-121.8725, 37.2075], "50.244.229.105": [-77.9005, 40.7915], "75.140.57.34": [-119.8105, 39.5295], "73.227.233.90": [-71.2195, 42.7915], "76.14.101.62": [-122.2925, 37.5405], "216.66.102.83": [-72.6625, 44.1095], "104.162.110.2": [-73.9525, 40.6485], "50.89.10.170": [-80.5925, 28.0305], "108.49.142.204": [-71.4405, 42.3315], "47.14.34.192": [-71.5705, 42.6675], "50.37.95.236": [-117.0025, 46.7285], "23.24.51.6": [-75.7695, 39.7795], "71.56.79.56": [-84.3185, 33.8495], "198.180.150.39": [-77.4605, 39.0215], "198.180.152.19": [-96.8205, 32.8015], "99.150.228.34": [-78.9395, 35.9915], "147.28.0.132": [-122.3385, 47.6075], "149.20.4.10": [-122.1405, 37.4395], "129.250.50.30": [-96.8195, 32.7975], "129.250.50.34": [-80.2295, 25.7885], "129.250.50.37": [-122.3395, 47.6095], "129.250.50.42": [-84.4195, 33.7705], "199.7.183.254": [-96.8595, 32.8105], "76.26.115.194": [-75.6095, 39.9585], "198.199.99.218": [-122.3995, 37.7195], "76.26.120.98": [-104.9785, 39.7375], "208.80.155.69": [-77.4885, 39.0385], "208.80.152.244": [-96.9285, 32.9885], "198.35.26.244": [-122.3985, 37.7195], "209.59.185.7": [-84.6685, 42.7105], "50.28.98.185": [-112.0125, 33.4175], "192.0.33.157": [-118.4015, 33.9195], "192.0.46.157": [-77.3715, 38.9475], "199.115.158.230": [-77.4605, 39.0175], "185.28.222.65": [-77.4905, 39.0395], "65.22.12.230": [-80.1905, 25.7805], "108.59.15.3": [-77.0205, 38.8995], "209.58.135.163": [-122.4205, 37.7705], "134.197.113.7": [-119.8225, 39.5375], "74.118.183.198": [-113.6225, 37.0815], "164.113.94.217": [-95.2625, 38.9505], "185.114.152.90": [-71.0615, 42.3485], "128.112.128.33": [-74.6515, 40.3485], "192.172.226.235": [-117.2415, 32.8815], "204.8.154.50": [-71.1115, 42.3475], "199.201.65.212": [-81.8715, 35.3305], "128.173.192.58": [-80.4105, 37.2005], "74.208.134.54": [-94.7505, 38.9305], "68.232.38.39": [-87.6305, 41.8815], "152.195.92.35": [-122.3295, 47.6095], "68.232.39.54": [-96.7995, 32.7795], "204.15.11.34": [-122.2895, 47.4995], "163.237.247.18": [-87.9685, 41.9975], "72.21.93.35": [-84.3885, 33.7495], "68.232.37.34": [-74.0085, 40.7105], "69.89.207.87": [-96.5185, 48.5805], "192.229.156.101": [-75.1685, 39.9515], "68.232.36.46": [-77.4885, 39.0415], "46.22.79.34": [-121.8885, 37.3375], "152.195.28.20": [-104.9885, 39.7385], "192.136.136.221": [-77.4305, 38.8875], "204.42.254.42": [-87.6205, 41.8485], "34.202.174.53": [-77.4905, 39.0395], "69.30.249.206": [-94.5795, 39.0985], "104.225.3.74": [-78.8795, 35.9315], "208.40.192.202": [-80.0385, 40.4315], "208.86.250.253": [-83.2585, 42.4515], "107.162.223.5": [-122.3625, 47.6205], "104.225.102.122": [-112.0125, 33.4215], "104.225.15.170": [-96.8825, 32.8415], "107.162.217.5": [-121.7825, 37.2375], "71.202.134.1": [-122.3325, 38.3305], "73.207.22.128": [-84.4085, 33.9615], "76.167.217.81": [-117.1985, 32.8595], "75.150.193.178": [-87.9985, 41.8795], "157.131.74.98": [-122.4785, 37.7895], "38.103.166.4": [-122.6825, 45.5185], "204.11.230.180": [-121.9425, 37.2795], "45.36.19.9": [-79.7925, 36.0685], "192.136.193.180": [-97.1525, 32.6705], "73.4.218.247": [-71.0615, 42.0385], "76.28.152.19": [-122.1215, 47.4775], "77.250.231.27": [-75.1715, 39.9485], "73.217.95.41": [-105.1715, 40.0995], "144.121.16.186": [-71.1015, 42.3695], "23.28.75.227": [-83.4615, 42.3215], "74.87.143.38": [-117.0005, 46.7285], "24.180.57.87": [-117.4005, 33.9485], "76.123.25.45": [-77.3805, 37.6775], "71.200.48.207": [-75.5205, 39.1605], "216.186.200.129": [-82.7595, 27.8575], "192.122.200.170": [-83.7395, 42.2485], "69.2.47.30": [-91.1195, 30.4515], "71.127.254.53": [-74.0095, 40.8875], "76.117.16.125": [-74.4285, 39.4905], "68.48.102.241": [-84.5685, 42.8375], "72.201.9.19": [-112.2885, 33.7095], "141.151.27.126": [-75.6085, 40.0915], "174.63.182.146": [-81.6425, 28.7975], "74.104.169.123": [-71.5225, 42.3085], "128.114.139.114": [-122.0725, 36.9985], "69.21.226.205": [-86.9825, 40.2005], "204.246.3.62": [-89.5325, 43.0685], "192.33.255.26": [-122.4025, 37.7195], "64.73.41.116": [-89.4325, 43.0115], "100.7.255.235": [-77.6515, 37.5085], "67.82.50.43": [-73.6315, 40.7305], "70.20.54.178": [-73.2005, 44.4685], "204.111.162.136": [-78.6705, 38.6495], "68.110.8.86": [-112.0705, 33.4505], "185.148.180.11": [-122.4005, 37.7805], "174.55.34.149": [-75.6505, 41.4915], "71.126.171.160": [-77.5295, 38.9785], "76.186.174.22": [-97.1095, 32.7395], "73.249.28.7": [-73.1295, 44.5285], "24.14.246.171": [-87.8995, 41.8915], "64.121.248.150": [-75.3385, 39.8585], "50.202.87.154": [-76.9885, 38.8895], "24.16.203.93": [-122.6385, 48.2905], "76.124.124.97": [-75.1585, 39.9475], "76.165.193.133": [-90.0785, 29.9495], "67.242.152.252": [-78.8785, 42.8915], "63.130.83.21": [-97.8225, 37.7505], "63.130.83.29": [-97.8225, 37.7505], "65.34.213.184": [-80.1425, 26.6095], "174.53.136.164": [-93.3625, 45.0315], "73.44.59.213": [-88.1105, 42.0075], "99.100.86.150": [-87.7905, 41.7385], "67.174.3.44": [-81.7305, 28.7985], "73.74.200.91": [-87.6905, 42.0695], "69.245.130.70": [-88.1405, 41.3195], "174.60.106.14": [-77.2305, 39.9775], "67.186.153.148": [-73.4305, 41.3585], "24.247.146.249": [-85.6205, 42.2995], "23.240.241.44": [-88.0905, 41.8405], "98.110.161.218": [-71.1395, 42.2785], "98.160.100.130": [-95.9895, 36.1495], "73.6.150.62": [-95.5995, 29.6695], "76.124.130.88": [-75.1695, 40.2015], "73.128.129.77": [-77.5995, 38.8105], "174.49.169.194": [-75.9185, 40.3495], "107.77.229.235": [-111.9085, 33.3805], "24.218.80.205": [-71.1085, 42.3705], "73.52.71.160": [-78.0185, 40.7915], "67.228.81.214": [-122.2905, 47.4875], "50.23.39.62": [-95.4305, 29.9405], "206.197.161.186": [-122.2095, 37.5015], "50.23.93.62": [-121.9595, 37.3795], "173.192.213.14": [-77.4695, 38.9095], "50.23.207.118": [-96.8295, 32.9305], "76.104.3.65": [-77.4885, 39.0385], "73.17.97.243": [-72.9685, 43.5685], "108.51.128.74": [-77.3885, 38.9695], "76.208.83.249": [-80.7925, 28.1995], "73.221.140.93": [-122.3105, 47.6185], "73.129.151.141": [-77.0005, 39.1075], "108.41.29.197": [-104.9785, 39.7375], "198.108.63.99": [-83.7425, 42.2795], "71.234.74.27": [-71.4585, 42.2895], "207.182.40.10": [-110.9325, 32.2195], "151.201.145.230": [-75.3925, 39.9175], "130.111.39.128": [-68.6725, 44.8815], "108.208.27.175": [-117.1585, 32.7375], "12.0.1.55": [-74.1395, 40.3975], "172.10.12.5": [-74.1425, 40.3685], "192.136.136.246": [-77.4625, 39.0195], "74.192.7.62": [-76.9685, 35.0675], "73.150.238.226": [-75.1825, 39.4175], "96.76.225.45": [-83.5925, 42.2585], "204.2.134.10": [-121.8915, 37.3415], "98.29.129.251": [-84.0915, 39.7415], "47.152.38.212": [-118.3415, 33.8395], "45.19.223.97": [-122.0815, 37.3905], "96.241.66.134": [-77.3105, 38.9675], "71.231.59.21": [-118.2385, 34.0485], "209.33.220.90": [-113.6215, 37.1195], "71.8.135.104": [-95.3885, 45.6515], "24.18.250.21": [-122.3025, 47.7595], "204.139.52.240": [-75.6605, 41.4105], "136.56.105.144": [-78.8785, 35.8595], "76.211.117.43": [-78.8485, 35.7305], "172.92.1.230": [-122.2405, 37.4885], "68.37.21.198": [-87.9405, 42.0705], "193.37.253.107": [-79.9625, 40.3675], "76.124.24.216": [-75.5385, 40.1795], "73.158.39.122": [-122.0985, 37.4015], "69.142.87.206": [-74.5725, 39.9885], "73.123.179.209": [-71.0425, 42.3705], "24.17.77.25": [-122.3215, 47.8175], "98.214.101.171": [-88.2795, 42.0375], "71.56.103.128": [-84.5395, 33.8275], "68.98.96.203": [-112.0725, 33.4475], "50.107.9.235": [-121.0525, 40.2985], "174.18.150.26": [-110.7525, 32.0795], "108.222.120.191": [-96.8225, 32.9815], "72.79.10.243": [-74.2625, 40.6995], "47.151.137.110": [-118.4625, 34.0005], "75.111.77.103": [-120.1815, 39.3275], "174.77.43.177": [-117.8315, 33.6795], "73.7.146.24": [-84.3905, 33.7495], "108.195.89.236": [-82.0405, 34.7405], "173.29.59.254": [-89.5305, 40.9005], "72.21.67.50": [-108.7605, 44.7515], "24.101.225.24": [-81.8595, 41.1375], "73.110.200.155": [-86.2695, 41.8205], "69.139.117.97": [-86.9385, 36.0575], "209.249.60.243": [-122.2625, 37.7695], "50.1.51.141": [-122.0315, 36.9705], "173.71.95.143": [-74.6685, 40.3605], "50.117.26.108": [-121.8925, 37.3275], "47.20.133.70": [-73.4125, 41.0895], "146.115.214.171": [-75.4225, 40.5305], "12.156.204.230": [-90.4725, 38.5415], "45.17.13.240": [-82.3615, 29.6775], "70.131.33.76": [-90.4915, 38.7775], "69.255.157.207": [-77.3915, 39.4475], "98.11.6.2": [-70.7215, 43.4795], "12.18.223.58": [-82.1485, 34.9375], "173.81.78.192": [-81.6025, 39.2785], "172.79.68.167": [-120.9015, 40.1205], "64.121.83.6": [-75.5405, 40.5985], "64.79.54.240": [-77.6305, 39.1915], "98.21.244.213": [-79.9995, 39.9995], "192.148.252.30": [-77.4625, 39.0205], "76.117.240.28": [-74.6425, 40.1315], "173.243.177.185": [-86.6305, 39.2315], "24.238.41.216": [-74.7495, 41.0585], "134.84.88.118": [-93.2295, 44.9715], "67.169.33.196": [-121.8895, 37.3415], "173.228.90.186": [-122.0225, 37.3675], "198.244.105.107": [-122.3325, 47.6175], "67.180.172.13": [-123.2215, 39.2575], "73.225.61.239": [-122.3115, 47.6785], "73.89.156.84": [-71.5505, 42.8775], "73.35.163.21": [-122.1905, 47.7185], "73.201.248.91": [-76.6495, 39.0615], "73.189.102.43": [-121.8895, 37.3375], "73.180.237.180": [-75.4495, 38.3985], "97.113.109.228": [-122.3885, 47.6775], "174.48.146.205": [-80.1485, 26.0095], "73.159.137.68": [-73.7085, 41.6205], "73.8.76.8": [-87.7285, 41.9615], "174.105.206.164": [-82.4585, 40.0685], "75.135.177.24": [-73.2885, 41.4885], "50.0.69.63": [-121.9725, 36.9475], "173.80.116.127": [-81.5615, 38.3705], "24.6.172.77": [-122.1115, 37.3915], "68.175.130.230": [-76.6715, 42.5415], "47.189.38.249": [-96.5495, 32.9215], "198.27.221.1": [-122.4885, 37.7815], "97.82.209.17": [-83.0405, 34.7585], "73.217.8.61": [-105.0905, 39.6485], "69.11.182.222": [-122.7395, 45.8985], "73.186.137.119": [-72.5895, 42.8415], "67.169.138.35": [-121.8325, 37.2315], "173.167.0.106": [-83.8915, 42.2575], "157.131.93.203": [-122.2715, 37.8795], "73.189.60.147": [-122.4185, 37.7695], "162.217.72.122": [-122.4205, 37.7705], "108.20.245.238": [-71.1125, 42.3715], "70.88.254.62": [-71.1115, 42.3675], "173.66.193.119": [-77.0715, 39.0015], "98.225.183.175": [-75.4015, 40.2175], "24.147.4.232": [-70.8705, 43.1715], "98.248.50.174": [-122.1085, 37.3875], "73.202.185.104": [-121.9025, 37.7595], "73.157.224.176": [-123.0225, 44.9285], "73.189.248.203": [-121.9315, 37.2785], "96.241.220.148": [-77.3305, 38.9415], "73.252.177.33": [-121.8605, 37.2785], "107.129.70.7": [-86.5595, 34.7405], "12.12.144.130": [-96.7085, 32.9885], "65.175.133.136": [-71.7385, 43.6415], "38.103.8.29": [-77.3825, 38.9575], "50.225.148.86": [-76.3925, 39.3315], "64.251.60.30": [-72.6915, 41.7695], "69.119.129.128": [-74.4285, 40.5405], "174.69.138.222": [-91.0885, 30.3605], "65.27.247.71": [-84.3185, 39.2815], "70.91.226.205": [-83.6705, 42.2205], "208.82.98.77": [-121.8995, 37.3275], "198.128.52.20": [-122.2525, 37.8795], "45.26.126.41": [-84.0915, 34.2615], "99.34.233.149": [-86.3905, 35.8475], "107.3.72.5": [-73.3905, 41.3895], "73.255.72.5": [-95.6195, 30.0405], "67.160.162.178": [-123.1095, 44.0575], "99.124.138.140": [-86.1595, 39.7675], "73.134.145.57": [-75.2195, 38.4605], "71.120.0.157": [-77.4185, 38.9575], "68.81.67.173": [-74.9885, 40.0515], "128.118.46.199": [-77.8715, 40.8095], "73.93.124.102": [-122.0715, 37.0505], "99.52.253.161": [-84.0815, 33.8695], "72.76.184.201": [-73.9915, 40.8615], "18.26.2.101": [-71.1195, 42.3795], "69.47.91.34": [-84.6505, 42.6485], "47.203.191.118": [-82.7305, 27.9285], "98.29.126.243": [-84.1795, 39.5595], "50.126.112.105": [-122.8095, 45.4905], "198.207.145.170": [-96.8795, 32.8215], "76.219.105.160": [-82.9095, 40.4175], "131.93.241.21": [-93.1785, 44.7075], "66.119.109.100": [-84.0525, 35.0685], "108.166.188.148": [-96.8225, 32.7995], "98.24.59.17": [-81.0415, 35.2385], "73.254.74.61": [-117.1495, 47.6595], "73.193.14.143": [-117.1695, 47.6505], "24.19.93.19": [-122.4825, 47.1785], "71.84.13.72": [-121.6315, 37.1205], "173.164.200.74": [-121.8515, 37.2205], "73.243.44.225": [-105.0215, 39.5385], "67.183.118.241": [-122.2305, 47.7585], "71.50.18.48": [-93.8505, 38.5895], "68.47.116.75": [-93.1615, 45.1495], "71.198.119.116": [-122.1705, 37.8575], "206.167.70.238": [-85.9105, 42.4205], "65.50.210.58": [-122.0895, 37.4215], "67.169.45.178": [-121.8485, 37.2185], "204.111.160.136": [-78.5625, 38.8195], "66.91.16.75": [-156.0225, 20.7805], "128.171.6.63": [-157.8215, 21.2975], "73.38.119.151": [-73.1705, 41.3215], "73.54.62.64": [-81.8805, 26.6375], "66.30.9.161": [-71.0895, 42.4005], "68.197.125.86": [-74.0185, 40.7595], "24.15.0.4": [-87.9385, 41.9005], "73.96.94.113": [-123.0885, 44.0475], "130.245.145.107": [-73.1185, 40.9085], "130.245.145.108": [-73.1285, 40.7875], "199.255.191.82": [-77.4625, 39.0195], "45.37.215.93": [-78.5015, 35.9695], "75.72.254.63": [-92.8615, 45.0715], "173.79.42.13": [-77.5315, 38.9915], "174.81.245.186": [-85.9885, 42.8905], "73.180.4.136": [-122.7915, 45.4485], "73.190.89.6": [-122.6405, 45.5695], "173.77.170.228": [-73.9885, 40.7205], "70.113.73.127": [-97.6505, 30.3785], "24.4.33.236": [-122.0225, 37.3195], "72.177.90.195": [-97.7985, 30.1685], "69.201.42.185": [-76.1425, 43.0515], "24.220.254.130": [-97.1115, 44.8985], "50.122.236.212": [-75.9005, 42.5375], "173.89.28.154": [-88.2305, 43.0085], "47.156.128.231": [-117.8905, 34.1015], "129.10.110.12": [-71.0895, 42.3385], "169.232.255.61": [-118.4485, 34.0705], "75.142.226.232": [-119.8915, 39.5505], "172.91.212.133": [-118.5405, 34.4615], "74.115.180.218": [-84.1895, 40.5675], "108.56.138.112": [-77.3495, 38.9305], "160.2.150.254": [-116.2195, 43.6515], "200.40.66.197": [-80.1885, 25.7685], "73.15.21.3": [-122.2685, 37.8685], "206.221.144.118": [-88.2305, 40.1095], "76.24.182.116": [-72.8405, 41.9175], "66.91.17.183": [-155.9995, 20.7695], "184.16.192.112": [-84.8585, 39.7415], "72.253.155.91": [-156.4985, 20.8775], "96.95.123.217": [-87.6495, 40.1185], "100.35.124.65": [-74.0295, 40.9895], "97.113.61.249": [-122.3385, 47.6115], "184.96.160.96": [-105.1395, 39.9875], "99.23.121.193": [-121.8205, 37.3675], "24.6.34.24": [-122.2725, 37.7995], "157.131.155.226": [-122.4295, 37.7485], "184.100.5.95": [-92.5585, 45.4005], "132.147.59.214": [-77.9685, 40.2215], "70.174.128.28": [-77.1525, 38.8375], "98.228.226.198": [-87.9825, 42.0915], "76.169.161.134": [-117.8305, 33.8715], "73.71.83.186": [-122.0795, 37.3875], "170.72.9.235": [-112.0225, 40.4915], "75.163.222.146": [-104.6885, 38.9285], "98.118.40.116": [-71.1425, 42.6585], "173.73.115.58": [-77.1525, 38.8375], "208.87.223.18": [-122.2325, 37.8395], "69.250.46.25": [-77.3515, 38.9285], "73.60.220.71": [-71.6285, 42.8575], "71.197.3.75": [-80.3985, 37.2185], "66.235.10.92": [-121.9685, 47.6305], "207.72.6.200": [-83.7385, 42.2505], "68.38.144.8": [-86.4915, 39.1695], "217.10.140.66": [-74.0115, 40.7205], "73.232.114.226": [-95.3715, 29.7615], "76.236.29.168": [-122.3885, 37.7805], "66.180.193.221": [-118.2615, 34.0485], "71.244.45.11": [-97.3025, 32.9495], "73.52.80.84": [-77.8805, 40.3805], "97.115.127.231": [-122.6895, 45.5585], "69.117.162.131": [-72.5325, 40.9885], "67.180.62.33": [-122.4195, 37.7695], "12.131.8.218": [-98.4905, 29.4295], "73.92.164.144": [-105.1025, 40.5775], "73.217.82.19": [-105.1225, 40.1395], "24.148.31.23": [-87.6315, 41.9095], "70.123.105.101": [-96.7615, 32.8615], "75.142.22.153": [-123.9415, 45.6115], "24.218.77.29": [-70.9385, 43.0775], "173.76.130.77": [-71.5525, 42.2175], "107.130.64.185": [-118.2425, 34.0485], "73.15.72.77": [-122.2425, 37.8405], "44.98.248.130": [-82.6405, 27.7675], "70.121.97.7": [-97.9295, 30.6875], "208.108.195.238": [-81.5995, 39.2815], "128.3.125.92": [-122.2685, 37.8715], "204.210.109.71": [-159.3505, 22.0805], "128.138.75.184": [-105.2595, 40.0095], "73.249.228.154": [-71.4895, 42.8705], "76.179.53.236": [-71.7985, 43.8605], "65.254.97.105": [-90.2505, 38.6415], "129.21.208.111": [-77.6785, 43.0805], "71.121.144.214": [-76.1885, 39.5115], "108.58.6.98": [-73.9405, 40.6875], "71.211.157.247": [-104.9925, 39.7405], "50.126.247.194": [-84.1915, 40.0285], "98.155.35.172": [-155.6705, 20.0085], "65.182.164.62": [-88.7295, 41.8715], "47.149.129.143": [-118.3385, 33.8375], "104.225.112.30": [-118.2585, 34.0505], "50.43.44.26": [-122.9415, 45.5175], "104.238.192.2": [-86.5215, 39.1705], "50.0.94.17": [-122.4605, 37.7615], "50.246.243.53": [-122.5895, 45.4885], "73.92.214.30": [-121.8695, 37.3885], "157.131.93.37": [-122.2715, 37.8815], "136.24.13.23": [-122.4305, 37.7705], "73.110.148.138": [-88.9505, 39.8685], "157.131.196.97": [-122.4305, 37.7585], "23.130.129.98": [-117.6095, 34.0685], "146.115.129.98": [-71.2095, 42.3495], "98.172.94.4": [-111.8915, 33.4295], "162.213.60.7": [-122.0195, 37.4085], "73.252.184.74": [-121.9985, 37.3185], "107.15.168.195": [-78.7105, 35.7415], "144.202.128.5": [-76.6315, 39.2815], "108.217.53.158": [-96.3805, 32.9415], "204.13.164.13": [-122.3395, 47.6075], "216.243.57.193": [-122.3415, 47.6175], "76.218.237.4": [-78.6405, 35.6995], "73.192.209.248": [-121.4285, 37.7415], "97.117.66.192": [-112.0415, 40.6275], "73.253.63.209": [-72.2505, 43.6395], "198.137.202.120": [-121.9225, 37.4675], "184.177.189.254": [-117.1585, 32.7195], "73.109.215.184": [-122.0825, 47.4895], "47.14.40.177": [-71.6025, 42.7605], "140.88.102.20": [-93.1625, 45.0515], "73.94.72.190": [-93.2025, 45.0785], "207.229.130.137": [-87.6615, 41.9575], "173.228.88.84": [-122.0805, 37.3905], "96.230.244.101": [-71.2405, 42.4085], "72.79.242.5": [-73.2005, 42.4795], "71.198.26.115": [-122.0205, 37.3905], "184.166.173.192": [-112.0305, 46.6005], "99.27.141.31": [-98.4395, 29.5285], "73.159.158.36": [-71.3795, 42.9405], "166.70.73.161": [-111.6895, 40.2805], "71.90.87.66": [-89.3685, 43.0815], "50.252.93.92": [-83.7525, 42.2795], "129.19.47.14": [-105.0785, 40.5885], "128.105.22.238": [-89.4085, 43.0715], "50.53.18.99": [-122.8885, 45.5085], "108.226.113.200": [-121.9215, 37.2875], "66.177.255.113": [-80.3615, 27.6495], "73.116.127.174": [-121.8115, 36.6505], "73.40.33.2": [-77.7105, 39.1285], "74.78.75.254": [-72.2785, 42.9285], "75.108.88.191": [-95.4625, 30.3095], "74.73.116.91": [-73.9415, 40.8295], "68.55.30.51": [-83.4915, 42.3815], "98.211.64.149": [-75.0685, 38.6885], "71.187.192.8": [-74.3485, 40.6405], "47.23.69.66": [-74.2485, 40.4315], "23.116.215.225": [-92.4315, 34.6595], "173.228.7.217": [-121.8905, 37.3275], "64.136.224.8": [-85.3305, 42.2385], "69.146.25.47": [-114.2805, 48.2205], "38.66.197.240": [-83.3295, 33.1615], "50.200.146.222": [-75.1885, 39.9375], "72.93.214.153": [-71.5385, 42.3095], "100.38.237.108": [-73.3325, 40.9185], "66.35.1.50": [-122.3425, 47.6075], "67.5.109.37": [-120.6025, 46.6685], "97.113.96.67": [-122.3015, 47.5585], "98.210.241.163": [-121.9115, 36.9715], "50.204.69.193": [-93.2515, 44.9975], "98.127.186.150": [-108.5815, 45.7975], "173.49.196.136": [-75.5395, 40.1795], "67.161.26.24": [-122.2385, 37.4705], "69.138.163.241": [-77.0325, 39.0015], "64.222.183.214": [-72.3115, 42.9585], "71.195.31.218": [-93.1305, 45.0685], "173.76.33.19": [-71.1495, 42.2315], "75.71.196.231": [-104.8995, 39.5295], "98.163.10.98": [-79.9025, 37.2975], "76.124.81.185": [-75.5995, 39.7375], "216.56.3.74": [-89.4085, 43.0675], "216.243.32.70": [-122.3525, 47.6185], "73.2.43.237": [-121.9425, 37.7005], "173.241.172.221": [-122.2595, 45.3985], "67.160.239.209": [-122.3195, 37.5695], "107.167.193.118": [-88.4425, 41.7595], "76.188.48.74": [-80.8015, 41.8615], "71.196.154.60": [-105.2985, 40.0415], "73.122.220.24": [-84.3885, 33.7815], "162.231.243.83": [-121.8895, 37.3415], "68.100.248.189": [-77.3985, 38.8585], "73.14.190.183": [-105.1585, 39.9805], "68.115.154.254": [-82.9805, 35.5285], "128.171.47.239": [-157.8205, 21.2995], "207.136.192.158": [-72.6505, 44.3405], "47.158.138.13": [-122.4205, 37.7705], "172.74.51.181": [-78.8225, 35.6075], "76.91.3.33": [-118.4285, 34.1405], "208.70.144.17": [-122.0825, 47.7395], "130.85.61.5": [-76.7125, 39.2575], "216.176.178.18": [-122.2895, 47.4895], "47.144.144.180": [-118.3885, 33.8605], "71.192.65.151": [-71.4725, 42.7715], "70.93.153.68": [-118.4525, 34.0375], "100.19.12.61": [-75.8815, 39.7675], "73.159.137.214": [-73.7415, 41.6685], "73.53.65.241": [-122.2815, 47.3275], "66.169.246.33": [-122.8795, 42.2995], "71.127.158.50": [-76.4985, 39.0305], "70.57.20.78": [-105.2225, 39.7485], "67.174.213.204": [-121.9525, 37.8395], "69.181.5.13": [-122.1205, 47.6685], "71.198.13.164": [-122.3895, 37.7875], "71.51.174.155": [-78.5825, 38.0595], "99.137.191.34": [-96.7125, 32.9805], "68.107.118.40": [-117.1615, 32.7085], "166.130.104.242": [-74.0015, 40.7405], "73.139.164.57": [-80.1195, 26.8595], "73.245.251.173": [-80.1595, 26.5705], "71.225.156.34": [-75.1725, 39.9515], "47.196.158.32": [-82.4715, 28.0685], "74.88.76.96": [-73.5395, 41.0415], "50.246.66.190": [-77.0425, 38.8995], "128.118.46.198": [-77.8705, 40.8075], "65.254.97.49": [-90.2505, 38.6405], "65.254.97.52": [-90.2495, 38.6415], "135.84.58.40": [-75.1995, 39.9615], "65.254.97.40": [-90.2485, 38.6295], "135.84.56.40": [-80.2085, 25.7885], "65.254.97.43": [-90.2485, 38.6375], "70.167.13.75": [-117.0705, 32.7695], "135.84.56.43": [-80.2105, 25.7905], "174.67.25.77": [-97.5725, 35.3485], "174.62.70.109": [-121.9685, 36.9775], "96.255.61.139": [-77.3015, 38.9495], "174.25.169.168": [-84.7785, 45.0415], "50.109.227.231": [-124.4225, 43.0515], "67.197.25.215": [-80.9005, 34.9875], "96.81.32.158": [-105.2195, 39.7475], "67.161.160.12": [-121.2585, 38.6815], "174.69.133.241": [-90.9915, 30.3505], "73.181.98.53": [-104.7895, 39.5875], "100.2.36.112": [-73.9485, 40.7875], "69.71.0.45": [-93.3185, 37.0575], "136.32.6.174": [-94.8325, 39.1605], "140.186.85.205": [-96.8115, 46.8195], "71.206.75.171": [-81.7815, 24.5595], "24.225.122.35": [-96.1885, 48.0975], "66.79.142.10": [-121.9585, 37.3885], "104.61.88.81": [-84.3315, 33.8295], "130.245.145.149": [-73.1395, 40.9305], "136.63.76.184": [-94.3285, 38.8995], "68.96.186.77": [-115.2785, 36.1715], "50.103.121.78": [-88.2505, 40.1075], "162.255.8.150": [-88.1005, 40.4595], "128.9.160.61": [-118.4495, 33.9775], "192.5.203.212": [-87.6615, 40.4595], "209.240.65.188": [-93.2705, 44.9785], "47.188.184.134": [-96.8885, 32.9785], "76.191.19.33": [-88.1985, 40.1015], "73.225.157.93": [-122.7705, 48.9005], "68.38.12.91": [-86.1105, 40.4685], "73.231.203.30": [-122.0205, 37.2705], "98.180.230.141": [-115.0305, 36.0375], "76.167.189.224": [-117.2005, 32.8515], "146.115.6.2": [-71.1685, 42.2905], "66.67.19.199": [-77.5925, 43.0715], "76.169.181.211": [-118.3795, 34.0495], "67.186.229.62": [-111.6825, 40.0105], "66.7.126.161": [-111.9205, 40.6115], "75.162.6.111": [-93.7095, 41.7685], "69.255.121.239": [-77.4295, 39.3785], "70.106.197.175": [-77.5215, 39.0495], "71.220.234.28": [-84.2805, 30.4405], "66.24.222.60": [-77.5815, 43.1575], "73.93.187.127": [-122.0605, 37.4215], "68.111.13.62": [-110.8885, 32.2095], "73.76.171.227": [-95.4525, 30.0595], "108.207.255.214": [-120.8705, 37.5995], "173.18.148.199": [-93.4685, 41.6385], "68.110.21.244": [-96.0725, 41.1275], "73.189.64.139": [-122.2695, 37.8885], "97.127.69.46": [-93.2795, 44.9905], "98.167.136.44": [-112.1015, 33.3905], "72.68.115.57": [-75.1015, 39.7115], "140.180.226.107": [-74.6515, 40.3215], "107.3.175.60": [-121.7905, 36.6805], "76.174.17.39": [-118.5395, 34.1975], "74.71.209.196": [-73.9885, 40.6575], "24.255.23.59": [-112.3585, 33.4915], "71.0.93.2": [-78.5585, 38.1495], "67.76.163.196": [-78.5625, 38.1515], "173.61.187.251": [-74.7905, 40.2595], "174.53.2.217": [-92.1185, 34.7375], "24.61.110.238": [-70.8625, 43.2695], "174.53.156.145": [-93.0115, 45.0895], "75.68.27.72": [-71.3705, 42.9395], "50.245.46.133": [-71.8825, 42.7395], "71.72.140.236": [-84.4515, 39.3675], "44.16.51.1": [-118.4025, 34.2605], "24.19.247.74": [-122.3525, 47.6175], "73.162.195.248": [-122.4215, 37.7715], "73.39.231.59": [-76.6215, 39.1605], "162.233.201.149": [-122.3005, 37.8675], "208.115.148.220": [-112.0485, 33.0585], "24.165.80.18": [-117.0685, 33.0005], "24.18.164.4": [-122.3325, 47.6075], "24.92.134.225": [-83.0615, 39.9915], "73.230.180.235": [-76.3305, 40.0115], "68.64.82.4": [-73.9995, 40.7375], "67.183.153.88": [-122.1695, 47.5505], "76.25.43.163": [-104.8795, 39.8905], "96.241.125.168": [-77.0885, 38.9795], "71.171.106.132": [-77.4885, 39.0375], "67.169.97.196": [-122.1625, 38.0475], "66.218.0.5": [-76.1515, 43.0475], "96.255.112.234": [-77.1115, 38.8795], "173.73.212.195": [-76.9885, 38.8995], "73.92.124.43": [-122.0315, 37.3195], "192.110.255.62": [-77.4595, 39.0195], "192.5.44.70": [-75.1925, 39.9475], "24.12.156.156": [-88.0025, 42.0495], "44.44.117.16": [-71.2225, 42.4505], "45.24.251.23": [-91.0005, 30.3615], "67.188.19.174": [-122.0495, 37.9585], "73.158.247.136": [-121.9495, 37.4015], "24.51.135.52": [-78.0225, 41.7685], "24.130.60.11": [-122.0415, 37.3715], "98.249.35.131": [-80.4315, 37.2715], "97.126.102.103": [-122.5185, 47.6205], "74.96.104.11": [-77.1885, 39.2585], "131.247.18.33": [-82.4105, 28.0585], "108.30.122.254": [-73.9805, 40.6905], "24.5.245.225": [-122.3295, 47.6075], "173.76.164.158": [-71.4395, 42.5775], "160.36.59.129": [-83.9195, 35.9595], "162.249.156.18": [-95.3725, 30.0985], "24.6.137.5": [-121.9605, 37.2385], "205.234.117.2": [-76.3115, 40.1685], "173.228.71.184": [-122.6715, 38.4305], "68.173.138.153": [-73.9905, 40.7185], "67.245.43.27": [-73.9705, 40.6905], "174.74.11.89": [-95.9325, 41.2585], "96.89.109.201": [-122.6515, 45.5285], "73.231.85.80": [-122.0715, 37.4305], "66.220.251.95": [-72.4995, 43.3175], "24.130.91.245": [-122.7985, 38.3385], "99.16.97.208": [-122.6285, 38.2195], "73.40.22.143": [-77.4085, 37.2475], "199.201.145.28": [-71.0795, 42.3815], "108.51.180.14": [-76.9885, 39.1105], "24.251.93.186": [-111.8925, 33.4005], "45.46.88.158": [-70.6815, 44.2015], "47.14.114.146": [-71.6015, 42.1695], "70.161.141.62": [-76.2915, 36.7795], "98.182.31.36": [-119.2205, 34.2985], "172.222.171.15": [-119.2695, 34.2675], "24.209.55.62": [-81.4695, 41.5095], "64.180.81.188": [-114.0795, 48.0395], "100.36.45.114": [-77.3605, 38.8995], "185.45.146.238": [-74.0025, 40.7415], "100.2.46.25": [-73.9825, 40.6715], "64.83.178.147": [-105.0115, 40.1995], "68.203.175.104": [-96.8405, 32.8005], "38.142.218.114": [-77.3405, 38.9475], "69.84.9.250": [-118.2405, 34.0495], "50.241.59.243": [-93.2285, 44.9485], "47.144.228.196": [-117.1625, 33.5695], "128.9.161.173": [-118.4415, 33.9785], "157.131.222.124": [-122.4185, 37.7505], "100.36.149.46": [-77.3085, 38.7915], "50.202.194.198": [-71.2185, 42.4475], "208.125.171.126": [-73.6185, 42.8085], "24.162.242.246": [-78.8785, 35.8315], "24.6.241.33": [-122.0615, 37.3785], "199.120.117.103": [-91.6385, 41.8485], "75.139.7.163": [-85.2725, 36.1495], "67.86.129.212": [-73.9625, 40.6815], "173.49.232.6": [-75.8615, 39.8005], "74.140.100.139": [-82.4905, 40.0415], "149.43.80.25": [-75.5385, 42.8275], "173.91.44.117": [-81.4625, 41.5295], "98.171.172.74": [-118.2715, 33.9685], "75.68.186.4": [-69.9705, 43.9095], "71.213.121.47": [-82.5085, 40.3305], "138.128.190.246": [-81.3905, 28.6215], "208.74.138.130": [-118.2595, 34.0485], "99.85.29.171": [-78.6415, 35.7795], "67.246.132.67": [-76.2615, 42.0995], "73.172.80.175": [-77.0185, 38.8785], "172.93.216.242": [-113.7895, 42.4985], "73.72.118.124": [-87.6895, 42.0475], "174.74.36.122": [-96.0485, 41.2315], "71.179.9.130": [-76.4125, 39.5085], "69.116.165.66": [-74.0405, 40.7395], "140.192.218.186": [-87.6305, 41.8795], "104.175.188.233": [-118.4095, 34.0205], "67.166.28.74": [-105.0195, 39.9185], "73.34.49.85": [-104.7295, 39.5995], "100.4.192.237": [-73.9385, 42.8085], "69.49.161.92": [-106.6485, 35.0985], "151.161.36.135": [-77.4585, 41.1395], "72.69.158.16": [-74.0025, 40.7385], "174.56.111.37": [-105.8505, 35.6185], "148.59.200.131": [-94.4695, 39.1675], "98.249.18.56": [-77.6125, 38.2075], "4.14.254.153": [-78.7885, 35.7315], "204.77.234.46": [-84.3915, 33.7805], "108.26.148.190": [-71.0515, 42.4605], "174.83.130.41": [-119.7205, 39.0415], "108.6.195.165": [-73.8525, 40.7195], "71.237.92.38": [-105.0815, 40.5875], "128.114.255.9": [-122.0615, 36.9905], "136.62.62.88": [-97.8415, 30.2005], "71.205.5.58": [-104.7205, 39.6205], "72.200.128.29": [-71.4495, 41.4495], "73.93.135.95": [-121.9995, 37.3705], "68.188.189.115": [-83.9495, 43.4215], "174.126.74.4": [-112.0695, 33.4505], "72.46.56.101": [-96.6385, 40.7775], "73.16.26.19": [-70.0985, 43.8575], "146.115.226.85": [-75.2385, 40.6705], "65.96.33.75": [-70.0985, 43.8595], "71.212.2.79": [-122.3325, 47.6115], "174.104.143.151": [-81.4415, 41.1615], "128.187.82.226": [-111.6515, 40.2515], "18.26.5.198": [-71.0895, 42.3575], "71.58.236.16": [-76.0485, 41.3495], "108.53.180.242": [-74.0785, 40.7285], "73.164.193.104": [-123.1095, 44.6385], "70.231.19.155": [-78.9085, 35.8505], "69.40.119.112": [-84.5825, 37.8805], "100.36.112.123": [-77.0525, 38.7995], "128.138.200.58": [-105.2625, 40.0115], "128.210.109.92": [-86.9085, 40.4185], "23.79.231.14": [-122.4125, 37.7875], "68.47.91.180": [-93.4625, 45.0685], "24.149.120.220": [-79.2625, 37.3915], "72.68.108.199": [-74.0305, 40.7375], "23.251.82.28": [-85.0805, 35.0685], "192.58.193.254": [-121.4905, 38.6485], "98.244.76.91": [-78.5805, 38.0595], "184.170.76.26": [-80.5795, 37.1285], "73.60.202.39": [-71.7985, 42.5815], "98.217.220.104": [-70.8925, 42.5285], "71.105.243.227": [-73.9025, 40.7695], "216.56.243.250": [-89.4725, 43.0585], "73.3.227.235": [-104.9925, 39.9085], "75.60.243.198": [-78.9405, 35.7875], "199.253.27.64": [-116.5705, 47.3215], "67.169.145.66": [-122.0285, 36.9705], "68.203.21.32": [-97.8185, 30.4395], "103.105.49.13": [-118.3885, 33.9505], "73.118.179.178": [-122.2285, 47.3815], "97.126.12.59": [-122.3925, 47.5375], "73.69.249.75": [-72.2525, 43.6385], "104.58.80.93": [-84.3905, 33.7505], "73.169.57.109": [-104.7295, 39.5005], "147.92.96.57": [-84.5695, 42.7405], "208.90.212.227": [-122.4185, 37.7575], "173.24.67.141": [-91.2025, 43.4185], "172.91.77.0": [-118.4515, 34.0395], "96.32.152.183": [-83.3905, 33.9205], "108.44.215.199": [-77.5595, 39.1195], "205.234.237.186": [-87.6285, 41.8805], "73.54.189.183": [-84.3385, 33.7175], "128.119.150.41": [-72.5185, 42.3705], "71.146.225.254": [-97.6425, 35.5585], "66.68.32.163": [-97.7225, 30.4015], "47.38.143.240": [-95.6615, 29.8995], "69.31.144.4": [-90.5605, 30.0695], "50.83.106.180": [-93.2325, 41.5995], "67.52.187.132": [-118.0025, 33.6605], "71.142.7.89": [-78.7825, 35.7895], "99.126.115.47": [-98.3315, 29.5875], "98.214.242.200": [-87.5205, 41.4885], "96.35.114.157": [-83.5305, 43.0195], "67.41.198.253": [-104.9405, 39.9415], "108.189.28.77": [-81.3395, 28.6975], "24.60.164.179": [-72.8685, 41.3175], "75.139.128.41": [-83.9985, 34.1085], "98.195.254.112": [-95.5385, 29.7775], "44.94.64.2": [-92.1025, 46.7875], "68.83.168.2": [-75.7525, 39.6815], "45.26.150.95": [-98.2315, 29.5585], "24.213.105.50": [-88.2715, 34.8185], "24.208.48.88": [-88.3115, 44.2305], "47.210.79.154": [-93.6915, 32.5815], "50.24.106.182": [-96.2915, 30.5785], "198.90.14.26": [-84.2215, 39.3895], "108.39.67.39": [-76.4715, 37.0615], "44.4.17.147": [-121.9205, 37.4685], "73.11.174.19": [-122.2105, 47.7605], "24.42.211.232": [-86.7505, 34.6995], "74.192.110.215": [-95.2995, 32.3485], "104.175.197.189": [-118.3995, 34.0195], "98.191.114.228": [-111.9795, 33.3175], "76.30.9.35": [-95.1795, 30.0015], "70.162.239.240": [-111.8385, 33.3075], "73.169.7.152": [-104.7585, 39.7975], "73.231.222.217": [-122.4125, 37.7995], "24.17.245.235": [-122.3295, 47.6075], "100.36.2.228": [-77.3585, 39.0275], "173.217.67.169": [-93.2025, 30.1975], "184.0.77.78": [-84.8925, 38.9915], "139.138.66.149": [-80.2415, 26.2875], "174.100.201.24": [-81.5915, 41.4885], "45.17.162.192": [-84.3905, 33.7795], "47.149.95.49": [-117.1205, 33.5085], "172.90.248.45": [-118.4005, 34.0705], "98.115.150.55": [-75.3095, 39.9795], "100.14.130.194": [-75.5195, 39.1595], "98.249.124.21": [-106.2195, 35.8205], "199.184.246.170": [-104.8895, 39.6175], "67.149.228.19": [-83.1595, 42.4985], "74.64.100.120": [-73.9695, 40.7905], "72.223.40.102": [-111.6795, 33.2715], "71.90.95.111": [-89.0085, 42.4085], "73.93.161.145": [-121.9425, 37.5495], "24.213.124.190": [-81.7825, 32.4515], "71.143.145.144": [-80.7215, 35.1185], "72.175.44.196": [-104.7605, 41.1375], "64.234.27.94": [-119.5505, 47.3175], "97.99.108.155": [-96.7815, 32.9875], "108.53.170.206": [-74.4015, 40.3915], "76.193.120.181": [-80.7705, 35.1315], "108.14.72.48": [-73.7795, 41.2675], "71.62.65.192": [-80.7795, 37.0515], "73.176.137.8": [-88.2395, 40.1215], "217.28.163.28": [-84.5685, 34.0385], "204.110.191.190": [-96.4985, 33.1715], "198.105.231.114": [-83.7285, 42.8005], "129.244.208.56": [-95.9425, 36.1495], "104.185.207.122": [-84.3395, 33.8695], "209.180.211.163": [-122.3985, 47.5715], "47.35.37.159": [-122.3025, 40.4475], "104.12.251.1": [-80.6605, 35.1685], "38.107.148.196": [-80.2205, 40.6205], "65.60.173.98": [-82.8095, 39.9975], "71.172.152.130": [-74.0785, 40.7285], "75.111.238.244": [-101.8615, 33.5775], "107.210.94.68": [-80.3015, 36.1315], "66.44.23.245": [-77.0705, 38.9475], "73.74.204.32": [-87.7495, 41.9685], "66.84.81.55": [-77.9625, 39.1005], "76.14.34.20": [-122.4205, 37.6505], "136.53.6.97": [-86.5795, 34.6085], "107.2.254.108": [-105.1195, 39.8795]}
    #
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


def search_candidats(list_page_info):
    '''
    select landmarks from cyberspace
    :param list_page_info: a list of info of web page, including ip, url, html
    :return:
    '''
    count_ambiguity = 0
    radius = 50000
    for page_info in pyprind.prog_bar(list_page_info):
        ip = page_info["ip"]
        ipinfo_fr_commercial_tools = get_coordinate_by_commercial_tools(ip) # filter
        if ipinfo_fr_commercial_tools is None:
            count_ambiguity += 1
            print("%s the city is ambiguous..." % ip)
            continue
        # coarse_grained_region = ipinfo_fr_commercial_tools["coarse_grained_region"]
        lng_com = float(ipinfo_fr_commercial_tools["longitude"])
        lat_com = float(ipinfo_fr_commercial_tools["latitude"])

        org_whois = online_search.get_org_name_by_whois_rws(ip)
        candidates_fr_whois = None

        query_whois = None
        if org_whois is not None:
            query_whois = org_whois
            candidates_fr_whois = geolocation.google_map_nearby_search(query_whois, lng_com, lat_com, radius)

        # coordi_fr_whois = coordi_fr_whois[0] if len(coordi_fr_whois) > 0 else None

        candidates_fr_page, query_page = get_candidates_by_page(page_info["html"], page_info["url"], lng_com, lat_com, radius)
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
    file_inp = open("../resources/schools_us_0.5.json", "r")
    list_page_info = json.load(file_inp)
    print(len(list_page_info))
    list_page_info = search_candidats(list_page_info)
    # # dict_landmarks = select_landmarks(list_page_info)
    # # print(json.dumps(dict_landmarks, indent=2))
    # # print(len(list(dict_landmarks.keys())))
    json.dump(list_page_info, open("../resources/schools_us_0.6.json", "w"))







