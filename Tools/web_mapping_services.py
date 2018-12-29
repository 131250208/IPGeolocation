from urllib import parse
import json
from Tools import geo_distance_calculator, mylogger
import logging
import settings
logger = mylogger.Logger("../Log/web_mapping_services.log", logging.INFO, logging.INFO)
from Doraemon.Requests import requests_dora as rt


def quote(queryStr):
    try:
        queryStr = parse.quote(queryStr)
    except:
        queryStr = parse.quote(queryStr.encode('utf-8', 'ignore'))

    return queryStr


def get_proxies():
    proxies = {
        "http": "http//127.0.0.1:1080",
        "https": "https://127.0.0.1:1080"
    }
    return proxies


def google_map_place_search(queryStr):
    '''
    invoke google map API: places searching
    fields=photos,formatted_address,name,opening_hours,rating
    :param queryStr:
    :return:
    '''
    # "&locationbias=circle:2000@47.6918452,-122.2226413" \
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?" \
          "input=%s&inputtype=textquery" \
          "&fields=formatted_address,name,opening_hours,rating" \
          "&key=%s" % (quote(queryStr), settings.GOOGLE_API_KEY)
    res_json = rt.try_best_2_get(url, proxies=get_proxies(), timeout=10, invoked_by=google_map_place_search.__name__)
    return json.loads(res_json.text)


def google_map_place_search_bias(query_str, lng, lat, radius):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?" \
          "input=%s&inputtype=textquery" \
          "&fields=formatted_address,name,opening_hours,rating" \
          "&locationbias=circle:%d@%f,%f" \
          "&key=%s" % (quote(query_str), radius, lat, lng, settings.GOOGLE_API_KEY)
    res_json = rt.try_best_2_get(url, proxies=get_proxies(), timeout=10, invoked_by=google_map_place_search_bias.__name__)
    return json.loads(res_json.text)


def google_map_nearby_search(query_str, lng, lat, radius):
    api = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?keyword=%s&location=%f,%f&radius=%d&key=%s" % (quote(query_str), lat, lng, radius, settings.GOOGLE_API_KEY)

    list_candidates = []
    while True:
        res_json = rt.try_best_2_get(api, proxies=get_proxies(), timeout=10, invoked_by=google_map_nearby_search.__name__)
        if res_json.status_code != 200:
            break
        res_json = json.loads(res_json.text)
        if "error_message" in res_json and "exceeded" in res_json["error_message"]:
            logger.info("api: google_map_nearby_search, exceeded daily limit")
            raise Exception

        for candidate in res_json["results"]:
            list_candidates.append({
                "query_str": query_str,
                "org_name": candidate["name"],
                "longitude": candidate["geometry"]["location"]["lng"],
                "latitude": candidate["geometry"]["location"]["lat"],
            })

        next_page_token = res_json["next_page_token"] if "next_page_token" in res_json else None
        if next_page_token is None:
            break
        api = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken=%s&key=%s" % (next_page_token, settings.GOOGLE_API_KEY)

    return list_candidates


def google_map_geocode_addr2coordinate(address):
    '''
    invoke google map API: geocoding
    :param address:
    :return:
    '''
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s" % (quote(address), settings.GOOGLE_API_KEY)
    res_json = rt.try_best_2_get(url, proxies=get_proxies(), timeout=10, invoked_by=google_map_geocode_addr2coordinate.__name__)
    return json.loads(res_json.text)


def google_map_geocode_coordinate2addr(longitude, latitude):
    latlng = str(latitude) + "," + str(longitude)
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s&key=%s" % (
    quote(latlng), settings.GOOGLE_API_KEY)

    res = rt.try_best_2_get(url, proxies=get_proxies(), timeout=10, invoked_by=google_map_geocode_coordinate2addr.__name__)
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


def google_map_get_coordinate(queryStr):
    '''
    get coordination by key words query
    :param queryStr: queryStr of the target place
    :return:
    '''
    candidates = google_map_place_search(queryStr)["candidates"]
    list_location_candidates = []
    for candidate in candidates:
        addr = candidate["formatted_address"]
        org_name = candidate["name"]
        results = google_map_geocode_addr2coordinate(addr)["results"]
        for r in results:
            list_location_candidates.append({
                "longitude": r["geometry"]["location"]["lng"],
                "latitude": r["geometry"]["location"]["lat"],
                "addr": addr,
                "org_name": org_name,
            })
    return list_location_candidates


def get_dis_btw_2places(query1, query2):
    r1 = google_map_get_coordinate(query1)
    r2 = google_map_get_coordinate(query2)

    if len(r1) > 0 and len(r2) > 0:
        dis = geo_distance_calculator.get_geodistance_btw_2coordinates(r1[0]["longitude"], r1[0]["latitude"], r2[0]["longitude"], r2[0]["latitude"])
    else:
        dis = -1
    print("place1: %s, place2: %s" % (r1, r2))
    return dis


def google_map_static_map(list_coord):
    '''
    :param list_coord: {"longitude": lng, "latitude": lat}
    :return: a url used to access a static map through browser
    '''
    list_coord_str = []
    for coord in list_coord:
        coord_str = "%f,%f" % (coord["latitude"], coord["longitude"])
        list_coord_str.append(coord_str)

    url = "https://maps.googleapis.com/maps/api/staticmap?language=en&size=2048x1280&maptype=roadmap&scale=4&zoom=4&key=AIzaSyBuvFKna_9YqhszzmGNV1MIFjGNnfz8uyk&markers=size:mid%7Ccolor:red%7C" + "%7C".join(list_coord_str)
    return url


if __name__ == "__main__":
    # list_prb = []
    # dict_probes = {'34759': [-122.0505, 47.5415], '33759': [-116.5705, 47.3215], '21031': [-108.5815, 45.7975], '25224': [-96.8115, 46.8195], '24899': [-84.7785, 45.0415], '15760': [-68.6695, 44.8675], '24908': [-124.4225, 43.0515], '32462': [-113.7895, 42.4985], '24971': [-105.2195, 39.7475], '24633': [-95.8415, 41.2585], '35561': [-82.8095, 39.9975], '10599': [-74.2285, 39.5815], '30352': [-121.9605, 37.2385], '11634': [-113.6215, 37.1195], '35620': [-101.8615, 33.5775], '35415': [-95.9425, 36.1495], '12180': [-86.9385, 36.0575], '2427': [-77.0215, 34.6705], '16951': [-118.0205, 33.7075], '12105': [-110.7525, 32.0795], '30263': [-99.4795, 27.5285], '35001': [-93.2025, 30.1975], '26946': [-84.2805, 30.4405], '24247': [-80.2105, 25.7905]}
    # for coord in dict_probes.values():
    #     list_prb.append({
    #         "longitude": coord[0],
    #         "latitude": coord[1],
    #     })
    # api = google_map_static_map(list_prb)
    # print(api)

    res = google_map_nearby_search("Amazon", -122.35689, 47.64288, 50000)
    # res = google_map_get_coordinate("Dongguan Guangdong")
    print(res)
    # print(len(res))