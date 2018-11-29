import json

import pyprind
from Tools import geo_distance_calculator, mylogger, commercial_db, web_mapping_services, purifier
from LandmarksCollector import owner_name_extractor as one, settings
logger = mylogger.Logger("../Log/iterative_inference_machine.py.log")
from itertools import combinations

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

    # print("%s finished..." % page_info["ip"])
    return page_info


def get_dis_2clusters(cluster1, cluster2):
    '''
    :param cluster1:
    :param cluster2:
    :return: max_dis, maximal distance btw random 2 candidates in two clusters
    '''
    max_dis = -1
    for c1 in cluster1:
        for c2 in cluster2:
            dis_c1_c2 = geo_distance_calculator.get_geodistance_btw_2coordinates(c1["longitude"], c1["latitude"],
                                                                     c2["longitude"], c2["latitude"])
            max_dis = dis_c1_c2 if dis_c1_c2 > max_dis else max_dis

    return max_dis


def merge_near_candidates(candidates_list, max_distance):
    if len(candidates_list) <= 1:
        return candidates_list

    candidates_list = [[c, ] for c in candidates_list]

    while True:
        pair_list = combinations(candidates_list, 2)
        dis_min = 9999999999
        pair_closest = None
        for pair in pair_list:
            dis = get_dis_2clusters(pair[0], pair[1])
            if dis < dis_min:
                dis_min = dis
                pair_closest = pair

        if dis_min > max_distance:
            break

        # merge candidates
        candidates_list.remove(pair_closest[0])
        candidates_list.remove(pair_closest[1])
        candidates_list.append(pair_closest[0] + pair_closest[1])

    candidates_list_new = []
    for can in candidates_list:
        if len(can) == 1:
            candidates_list_new.append(can[0])
        else:
            names = [c["org_name"] for c in can]
            name_merged = " + ".join(names)

            can = geo_distance_calculator.get_stdev_coordinates(can)[1]
            can["org_name"] = name_merged
            candidates_list_new.append(can)

    return candidates_list_new


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
        # logger.war(json.dumps(output, indent=2))

        threshold = 20000
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

    file = open("H:\\Projects/data_preprocessed/pages_us_with_candidates_0.1.json", "r")
    list_page_info = []
    count_landmarks = 0

    dict_landmarks_total = {}
    for line in file:
        list_page_info.append(json.loads(line))
        if len(list_page_info) == 10000:
            dict_landmarks = generate_landmarks(list_page_info)
            # print(json.dumps(dict_landmarks, indent=2))
            len_lm = len(list(dict_landmarks.keys()))
            dict_landmarks_total = {**dict_landmarks, **dict_landmarks_total}
            print(len_lm)
            count_landmarks += len_lm
            list_page_info.clear()

    dict_landmarks = generate_landmarks(list_page_info)
    len_lm = len(list(dict_landmarks.keys()))
    print(len_lm)
    print(len(dict_landmarks_total))
    json.dump(dict_landmarks_total, open("../Sources/landmarks_fr_cyberspace_0.1.json", "w"))

    print("total: %d" % count_landmarks)

    pass







