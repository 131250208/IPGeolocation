from math import radians, cos, sin, asin, sqrt
from Tools import settings
from Tools import requests_tools as rt
from urllib import parse
import json
import re
import datx
import requests
from Tools import mylogger
logger = mylogger.Logger("../Log/geolocation.py.log")


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
    res_json = rt.try_best_request_get(url, 5, "google_map_places_search", "abroad")
    return json.loads(res_json.text)


def google_map_geocode_addr2co(address):
    '''
    invoke google map API: geocoding
    :param address:
    :return:
    '''
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s" % (quote(address), settings.GOOGLE_API_KEY)
    res_json = rt.try_best_request_get(url, 5, "google_map_geocode_addr2co", "abroad")
    return json.loads(res_json.text)


def google_map_geocode_co2addr(longitude, latitude):
    latlng = str(latitude) + "," + str(longitude)
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s&key=%s" % (
    quote(latlng), settings.GOOGLE_API_KEY)

    res = rt.try_best_request_get(url, 5, "google_map_geocode_co2addr", "abroad")
    if res is None:
        return None
    res_json = json.loads(res.text)

    # print(json.dumps(res_json, indent=2))
    results = res_json["results"]
    result_top = results[0] if len(results) >= 1 else None
    if result_top is None:
        return None

    addr = {}
    address_components = result_top["address_components"]
    for comp in address_components:
        type = comp["types"][0]
        if type == "country" or "administrative_area_level" in type:
            addr[type] = comp["long_name"]

    return addr


def google_map_coordinate(queryStr):
    '''
    get coordination by key words query
    :param queryStr:
    :return:
    '''
    candidates = google_map_places_search(queryStr)["candidates"]
    list_location_candidates = []
    for candidate in candidates:
        results = google_map_geocode_addr2co(candidate["formatted_address"])["results"]
        for r in results:
            list_location_candidates.append(r["geometry"]["location"])
    return list_location_candidates


def ip_geolocation_ipinfo(ip):
    '''
    ip info from ipinfo.io
    :param ip:
    :return:json
    {
      "ip": "8.8.8.8",
      "city": "Mountain View",
      "region": "California",
      "country": "US",
      "loc": "37.3860,-122.0840", (lat, lon)
      "longitude": "-122.0840",
      "latitude": "37.3860",
      "postal": "94035",
      "phone": "650"
    }
    '''
    api = "http://ipinfo.io/%s/geo" % ip
    res = requests.get(api, headers=rt.get_random_headers(), timeout=10)
    json_res = json.loads(res.text)
    loc = json_res["loc"].split(",")
    json_res["longitude"] = loc[1]
    json_res["latitude"] = loc[0]
    return json_res


def ip_geolocation_ipip(ip):
    '''
    :param ip:
    :return: list
    [
        "GOOGLE.COM", // country_name
        "GOOGLE.COM", // region_name
        "",             // city_name
        "google.com", // owner_domain
        "level3.com", // isp_domain
        "", // latitude
        "", // longitude
        "", // timezone
        "", // utc_offset
        "", // china_admin_code
        "", // idd_code
        "", // country_code
        "", // continent_code
        "IDC", // idc
        "", // base_station
        "", // country_code3
        "", // european_union
        "", // currency_code
        "", // currency_name
        "ANYCAST" // anycast
        ]
    '''
    c = datx.City(settings.IP_INFO_IPIP_PATH)
    res = c.find(ip)

    return {
        "country": res[0] if len(res) >= 1 else "",
        "region": res[1] if len(res) >= 2 else "",
        "city": res[2] if len(res) >= 3 else "",
        "owner": res[3] if len(res) >= 4 else "",
        "isp": res[4] if len(res) >= 5 else "",
        "latitude": res[5] if len(res) >= 6 else "",
        "longitude": res[6] if len(res) >= 7 else "",
        "timezone": res[7] if len(res) >= 8 else "",
        "utc_offset": res[8] if len(res) >= 9 else "",
        "china_admin_code": res[9] if len(res) >= 10 else "",
        "idd_code": res[10] if len(res) >= 11 else "",
        "country_code": res[11] if len(res) >= 12 else "",
        "continent_code": res[12] if len(res) >= 13 else "",
        "idc": res[13] if len(res) >= 14 else "",
        "base_station": res[14] if len(res) >= 15 else "",
        "country_code3": res[15] if len(res) >= 16 else "",
        "european_union": res[16] if len(res) >= 17 else "",
        "currency_code": res[17] if len(res) >= 18 else "",
        "currency_name": res[18] if len(res) >= 19 else "",
        "anycast": res[19] if len(res) >= 20 else "",
    }


def geodistance(lng1, lat1, lng2, lat2):
    '''
    python计算两点间距离-m
    :param lng1: float
    :param lat1:
    :param lng2:
    :param lat2:
    :return:
    '''
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    dlon = lng2-lng1
    dlat = lat2-lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    dis = 2 * asin(sqrt(a)) * 6371 * 1000
    return dis

if __name__ == "__main__":
    # Mercer County
    # New Jersey
    res = google_map_coordinate("Palo Alto Research Center")
    print(res)
    # dis = geodistance(res[0]["lng"], res[0]["lat"], -117.39, 33.95)
    # print(dis)
    res = google_map_coordinate("Palo Alto Research Center Incorporated Santa Clara County") # Research Center Incorporated,  - PARC
    print(res)
    pass

    # count = 0
    #

    # for lm in landmarks:
    #     ip = lm["ip"]
    #     ipinfo = ip_geolocation_ipip(ip)
    #     country = ipinfo[0]
    #     ISP = ipinfo[4]
    #     if ISP not in cloud_providers:
    #         print(ipinfo)
    #         count += 1
    #         lon_ipinfo = ipinfo[6]
    #         lat_ipinfo = ipinfo[5]
    #         lon_planetlab = lm["longitude"]
    #         lat_planetlab = lm["latitude"]
    #         print("url: %s, ISP: %s, country_ipip: %s, country_ipinfo: %s, coordination_ipip: (%s, %s), coordination_planetlab: (%s, %s)" % (lm["url"], ISP, country, lm["country"], lon_ipinfo, lat_ipinfo, lm["longitude"], lm["latitude"]))
    #         if lon_ipinfo != "" and lat_ipinfo != "" and lon_planetlab != "" and lat_planetlab != "":
    #             dis = geodistance(float(lon_ipinfo), float(lat_ipinfo), float(lon_planetlab), float(lat_planetlab))
    #             print(dis / 1000)
    #
    # print(count)
    # candidates = google_map_coordinate("百度 US")
    # print(candidates)
    # print(geodistance(-88.5580, 47.1158, -88.5463, 47.1181))


