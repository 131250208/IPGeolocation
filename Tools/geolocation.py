from math import radians, cos, sin, asin, sqrt
import requests
from Tools import settings
from Tools import requests_tools as rt
from urllib import parse
import json
import re

def quote(queryStr):
    try:
        queryStr = parse.quote(queryStr)
    except:
        queryStr = parse.quote(queryStr.encode('utf-8', 'ignore'))

    return queryStr

def google_map_places_search(queryStr):
    '''
    invoke google map API: places searching
    fields=photos,formatted_address,name,opening_hours,rating
    :param queryStr:
    :return:
    '''
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?" \
          "input=%s&inputtype=textquery" \
          "&fields=formatted_address,name,opening_hours,rating" \
          "&key=%s" % (quote(queryStr), settings.GOOGLE_API_KEY)
    res_json = requests.get(url, headers=rt.headers, proxies=rt.get_proxies_abroad(), timeout=10)
    return json.loads(res_json.text)

def google_map_geocoding(address):
    '''
    invoke google map API: geocoding
    :param address:
    :return:
    '''
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s" % (quote(address), settings.GOOGLE_API_KEY)
    res_json = requests.get(url, headers=rt.headers, proxies=rt.get_proxies_abroad(), timeout=10)
    return json.loads(res_json.text)


def google_map_coordinate(queryStr):
    candidates = google_map_places_search(queryStr)["candidates"]
    list_location_candidates = []
    for candidate in candidates:
        results = google_map_geocoding(candidate["formatted_address"])["results"]
        for r in results:
            list_location_candidates.append(r["geometry"]["location"])
    return list_location_candidates

def ip_geolocation(ip):
    api = "http://ipinfo.io/%s/geo" % ip
    res = requests.get(api, headers=rt.get_random_headers(), timeout=10)
    return json.loads(res.text)


#python计算两点间距离-m
def geodistance(lng1, lat1, lng2, lat2):
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    dlon = lng2-lng1
    dlat = lat2-lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    dis = 2 * asin(sqrt(a)) * 6371 * 1000
    return dis


def loc_lm_planetlab_us():
    import socket
    import pyprind
    # landmarks_filtered = []
    #
    # for lm in pyprind.prog_bar(landmarks):
    #     url = lm["url"]
    #     name = re.sub("http://", "", url)
    #     name = re.sub("https://", "", name)
    #
    #     if "/" in name:
    #         name = name.split("/")[0]
    #     try:
    #         ip = socket.gethostbyname(name)
    #         lm["ip"] = ip
    #         json_location = ip_geolocation(ip)
    #         lm["city"] = json_location["city"]
    #         lm["region"] = json_location["region"]
    #         lm["country"] = json_location["country"]
    #         landmarks_filtered.append(lm)
    #     except Exception as e:
    #         print(e)
    #         print(url)
    pass

def get_all_lm():
    # landmarks = json.load(open("../sources/landmarks_planet_lab_us.json", "r"))
    # map_ip_coordinate = {}
    # data = []
    #
    # url = "https://atlas.ripe.net:443/api/v2/probes/?country_code=US"
    # while True:
    #     res = requests.get(url)
    #     probes = json.loads(res.text)
    #
    #     for r in probes["results"]:
    #         coordinates = r["geometry"]["coordinates"]
    #         ip = r["address_v4"]
    #         map_ip_coordinate[ip] = coordinates
    #         data.append({"name": ip, "value": 50})
    #
    #     next_page = probes["next"]
    #     if next_page is None:
    #         break
    #     else:
    #         url = next_page
    #
    # for lm in landmarks:
    #     map_ip_coordinate[lm["ip"]] = [lm["longitude"], lm["latitude"]]
    #     data.append({"name": lm["ip"], "value": 200})
    # print(json.dumps(map_ip_coordinate))
    # print("-------------------------")
    # print(json.dumps(data))
    pass

if __name__ == "__main__":
    candidates = google_map_coordinate("百度 US")
    print(candidates)
    # print(geodistance(-88.5580, 47.1158, -88.5463, 47.1181))


