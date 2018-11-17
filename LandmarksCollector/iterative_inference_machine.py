import json

import pyprind
from Tools import geo_distance_calculator, mylogger, commercial_db, web_mapping_services, purifier
from LandmarksCollector import owner_name_extractor as one, settings
logger = mylogger.Logger("../Log/iterative_inference_machine.py.log")


def get_candidates_by_owner_name_fr_pageinfo(html, url, lng, lat, radius):
    '''
    construct query string from web page and coarse_grained_region
    :param html:
    :param url:
    :param coarse_grained_region:
    :return: query string
    '''
    candidates = []
    it = one.get_org_info_fr_pageinfo(html, url)

    last_query = ""
    while True:
        try:
            org_info = next(it)
        except StopIteration:
            break
        query = purifier.filter_out_redundant_c(org_info, settings.REDUNDANT_LIST_QUERY)
        candidates = web_mapping_services.google_map_nearby_search(query, lng, lat, radius)
        last_query = query
        if len(candidates) > 0:
            break

    if len(candidates) > 0:
        return candidates, last_query
    return [], last_query


def search_candidates(page_info, lng_com, lat_com, radius,):
    '''
    use owner name to search candidates of specific IP
    :param page_info:
    :param lng_com: longitude from commercial databases
    :param lat_com: latitude from commercial databases
    :param radius:
    :return: a page info object with candidates got from searching by owner names
    '''
    query_registration_db = one.get_org_name_by_registration_db(page_info["ip"])
    query_registration_db = purifier.filter_out_redundant_c(query_registration_db, settings.REDUNDANT_LIST_QUERY)

    candidates_fr_registration_db = web_mapping_services.google_map_nearby_search(query_registration_db, lng_com, lat_com,
                                                                           radius) if query_registration_db is not None else []

    candidates_fr_pageinfo, query_page = get_candidates_by_owner_name_fr_pageinfo(page_info["html"], page_info["url"], lng_com, lat_com,
                                                                              radius)

    page_info["result_fr_page"] = {
        "query": query_page,
        "candidates": candidates_fr_pageinfo
    }
    page_info["result_fr_registration_db"] = {
        "query": query_registration_db,
        "candidates": candidates_fr_registration_db,
    }

    return page_info


def generate_landmarks(list_inference_info):
    '''
    select an exact location for each IP and return a landmark
    :param list_inference_info:
    :return: landmark: a dict from IP to coordinate
    '''
    huge_num = 99999999999
    dict_landmark = {}

    for info in list_inference_info:
        ip = info["ip"]
        try:
            lat_com = info["result_fr_commercial_tool"]["latitude"]
            lng_com = info["result_fr_commercial_tool"]["longitude"]
            candidates_fr_registration_db = info["result_fr_registration_db"]["candidates"]
            query_registration_db = info["result_fr_registration_db"]["query"]
            candidates_fr_page = info["result_fr_page"]["candidates"]
            query_page = info["result_fr_page"]["query"]
            ipinfo_fr_commercial_tools = info["result_fr_commercial_tool"]
        except KeyError:
            continue

        dis_registration_db2ipip = geo_distance_calculator.get_geodistance_btw_2coordinates(lng_com, lat_com, candidates_fr_registration_db[0]["longitude"],
                                                                                  candidates_fr_registration_db[0]["latitude"]) if candidates_fr_registration_db and len(
            candidates_fr_registration_db) == 1 else huge_num
        dis_pageinfo2ipip = geo_distance_calculator.get_geodistance_btw_2coordinates(lng_com, lat_com, candidates_fr_page[0]["longitude"],
                                                                                     candidates_fr_page[0]["latitude"]) if candidates_fr_page and len(
            candidates_fr_page) == 1 else huge_num
        dis_page2registration_db = geo_distance_calculator.get_geodistance_btw_2coordinates(candidates_fr_registration_db[0]["longitude"], candidates_fr_registration_db[0]["latitude"],
                                                                                  candidates_fr_page[0]["longitude"], candidates_fr_page[0]["latitude"]) \
            if candidates_fr_page and len(candidates_fr_page) == 1 and candidates_fr_registration_db and len(candidates_fr_registration_db) == 1 else huge_num

        # show result
        output = {
            "ip": ip,
            "coordinate_fr_commercial_tools": {
                "longitude": ipinfo_fr_commercial_tools["longitude"],
                "latitude": ipinfo_fr_commercial_tools["latitude"]
            },
            "registration_db": {
                "query": query_registration_db,
                "coordinate": candidates_fr_registration_db,
                "dis_registration_db2com": dis_registration_db2ipip,
            },
            "page": {
                "query": query_page,
                "coordinate": candidates_fr_page,
                "dis_page2com": dis_pageinfo2ipip,
            },
            "dis_pageinfo2registration_db": dis_page2registration_db,
        }
        logger.war(json.dumps(output, indent=2))

        threshold = 10000
        if dis_registration_db2ipip <= threshold or dis_pageinfo2ipip <= threshold:
            lng = None
            lat = None
            if dis_pageinfo2ipip < dis_registration_db2ipip:
                lng = candidates_fr_page[0]["longitude"]
                lat = candidates_fr_page[0]["latitude"]
            else:
                lng = candidates_fr_registration_db[0]["longitude"]
                lat = candidates_fr_registration_db[0]["latitude"]
            dict_landmark[ip] = [lng, lat]
    return dict_landmark


if __name__ == "__main__":

    # dict_landmarks = generate_landmarks(list_page_info)
    # print(json.dumps(dict_landmarks, indent=2))
    # print(len(list(dict_landmarks.keys())))
    pass







