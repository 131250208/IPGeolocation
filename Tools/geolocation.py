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
import geoip2.database
from Tools.IPLocate import IP

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
        addr = candidate["formatted_address"]
        org_name = candidate["name"]
        results = google_map_geocode_addr2co(addr)["results"]
        for r in results:
            list_location_candidates.append({
                "longitude": r["geometry"]["location"]["lng"],
                "latitude": r["geometry"]["location"]["lat"],
                "addr": addr,
                "org_name": org_name,
            })

    return list_location_candidates


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


def dis_btw_2p(query1, query2):
    r1 = google_map_coordinate(query1)
    r2 = google_map_coordinate(query2)

    if len(r1) > 0 and len(r2) > 0:
        dis = geodistance(r1[0]["longitude"], r1[0]["latitude"], r2[0]["longitude"], r2[0]["latitude"])
    else:
        dis = -1
    print("place1: %s, place2: %s" % (r1, r2))
    return dis


def stdev_coordinates(coordinates):
    if len(coordinates) == 0:
        return None
    exp_lat = 0
    exp_lng = 0
    for co in coordinates:
        if co["longitude"] is None or co["latitude"] is None:
            return None
        exp_lng += co["longitude"]
        exp_lat += co["latitude"]
    exp_lng = exp_lng / len(coordinates)
    exp_lat = exp_lat / len(coordinates)

    dis = 0
    for co in coordinates:
        dis += geodistance(co["longitude"], co["latitude"], exp_lng, exp_lat)
    return dis / len(coordinates), {"longitude": exp_lng, "latitude": exp_lat}


reader_ipplus = geoip2.database.Reader('../resources/GeoLite2-City.mmdb')
def ip_geolocation_geolite2(ip):
    res = reader_ipplus.city(ip)
    return {
        "country": res.country.name,
        "region": res.subdivisions.most_specific.name,
        "city": res.city.name,
        "longitude": res.location.longitude,
        "latitude": res.location.latitude
    }


def ip_geolocation_ipstack(ip): # not free, 10000/month
    api = "http://api.ipstack.com/%s?access_key=%s" % (ip, "a9b953df82f98f0169d1bbefe67f42d9")
    res = rt.try_best_request_get(api, 5, "ip_geolocation_ipstack")
    json_res = json.loads(res.text)
    return {
        "country": json_res["country_name"] if json_res["country_name"] is not None else "",
        "region": json_res["region_name"] if json_res["region_name"] is not None else "",
        "city": json_res["city"] if json_res["city"] is not None else "",
        "longitude": json_res["longitude"] if json_res["longitude"] is not None else "",
        "latitude": json_res["latitude"] if json_res["latitude"] is not None else "",
    }


def ip_geolocation_ipinfo(ip): # not free, 1000/day
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
    if json_res["loc"] == "":
        json_res["longitude"] = None
        json_res["latitude"] = None
    loc = json_res["loc"].split(",")
    json_res["longitude"] = float(loc[1])
    json_res["latitude"] = float(loc[0])
    return json_res


reader_ipip = datx.City(settings.IP_INFO_IPIP_PATH)
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

    res = reader_ipip.find(ip)

    return {
        "country": res[0] if len(res) >= 1 else "",
        "region": res[1] if len(res) >= 2 else "",
        "city": res[2] if len(res) >= 3 else "",
        "owner": res[3] if len(res) >= 4 else "",
        "isp": res[4] if len(res) >= 5 else "",
        "latitude": float(res[5]) if len(res) >= 6 and res[5] != "" else None,
        "longitude": float(res[6]) if len(res) >= 7 and res[6] != "" else None,
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


def ip_geolocation_ipplus360(ip):
    test = IP()
    test.load_dat("../resources/IP_trial_2018M11_single_WGS84.dat")
    result = test.locate_ip(ip)
    return {
        "continent": result[2],
        "country": result[5],
        "region": result[6],
        "city": result[7],
        "longitude": float(result[9]) if result[9] != "" else None,
        "latitude": float(result[10]) if result[10] != "" else None,
    }


if __name__ == "__main__":
    print(google_map_coordinate("Amazon ASHBURN"))
    print(google_map_coordinate("Amazon Ashburn"))
    # print(dis_btw_2p("Amazon AWS: Ashburn Data Center", "Amazon Ashburn"))
    pass

    # uniform the data type of coordinate

    # print(google_map_places_search("Microsoft Boydton"))# Redmond, Boydton
    # print(google_map_places_search("Microsoft Virginia Washington"))






