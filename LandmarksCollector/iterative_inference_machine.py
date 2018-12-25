from Tools import geo_distance_calculator, mylogger, web_mapping_services, ner_tool
from LandmarksCollector import owner_name_extractor as one
import enumeration
import settings, strings
logger = mylogger.Logger("../Log/iterative_inference_machine.py.log")
from itertools import combinations
import numpy as np


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
        query = ner_tool.filter_out_company_char(org_info)
        candidates = web_mapping_services.google_map_nearby_search(query, lng, lat, radius)
        last_query = query
        if len(candidates) > 0:
            break

    if len(candidates) > 0:
        return candidates, last_query
    return [], last_query


def search_candidates(sample, radius):
    '''
    use owner name to search candidates of specific IP
    :param sample:
    :param lng_com: longitude from commercial databases
    :param lat_com: latitude from commercial databases
    :param radius:
    :return: a page info object with candidates got from searching by owner names
    '''

    coarse_grained_loc_list = sample[strings.KEY_LOCS_FROM_COMMERCIAL_TOOLS]
    candidates_fr_searching = []

    org_name_list = sample[strings.KEY_POTENTIAL_OWNER_NAMES]

    org_name_list = [org_name for org_name in org_name_list if org_name is not None]
    # filer out duplicates
    org_name_list = sorted(org_name_list, key=lambda x: len(x), reverse=True)
    org_name_list_new = []
    mem = ""
    for s in org_name_list:
        if s.lower() not in mem.lower():
            org_name_list_new.append(s)
            mem += " %s" % s
    org_name_list = org_name_list_new

    # merge near coarse locs
    coarse_grained_loc_list = geo_distance_calculator.merge_near_locations(coarse_grained_loc_list, settings.MIN_DIS_BTW_DIF_COARSE_LOCS)
    for loc in coarse_grained_loc_list:
        lng_com = loc["longitude"]
        lat_com = loc["latitude"]
        for org_name in org_name_list:
            if org_name.strip() == "":
                continue
            candidates_fr_searching += web_mapping_services.google_map_nearby_search(org_name,
                                                                                    lng_com, lat_com, radius)

    sample[strings.KEY_CANDIDATES] = candidates_fr_searching

    return sample


def merge_near_candidates(candidates_list, max_distance):
    len_candidates = len(candidates_list)
    if len_candidates <= 1:
        return candidates_list

    clusters_list = [{"index": ind, "cluster": [{"index": ind, "candidate": c}, ], } for ind, c in enumerate(candidates_list)]

    dis_candidates = list(np.zeros([len_candidates, len_candidates], dtype=float).tolist())
    pair_list = combinations(clusters_list, 2)
    for pair in pair_list:
        c1 = pair[0]["cluster"][0]
        c2 = pair[1]["cluster"][0]
        dis = geo_distance_calculator.get_geodistance_btw_2coordinates(c1["candidate"]["longitude"], c1["candidate"]["latitude"],
                                                                 c2["candidate"]["longitude"], c2["candidate"]["latitude"])
        dis_candidates[c1["index"]][c2["index"]] = dis

    dis_clusters = dis_candidates[:]

    while True:
        pair_list = combinations(clusters_list, 2)
        dis_min = 9999999999
        pair_closest = None
        for pair in pair_list:
            cluster1 = pair[0]
            cluster2 = pair[1]
            dis = dis_clusters[cluster1["index"]][cluster2["index"]]

            if dis < dis_min:
                dis_min = dis
                pair_closest = pair

        if dis_min > max_distance:
            break

        # merge 2 clusters to the first cluster and update the dis_clusters matrix
        cluster1 = pair_closest[0]
        cluster2 = pair_closest[1]
        clusters_list.remove(cluster2)
        cluster1["cluster"] += cluster2["cluster"]

        ind_1 = cluster1["index"]
        ind_2 = cluster2["index"]
        for i in range(len_candidates):
            new_dis = dis_candidates[ind_1][i] if dis_candidates[ind_1][i] > dis_candidates[ind_2][i] else dis_candidates[ind_2][i]
            dis_clusters[ind_1][i] = new_dis
            dis_clusters[i][ind_1] = new_dis

    candidates_list_new = []
    for cluster in clusters_list:
        cluster = cluster["cluster"]
        if len(cluster) == 1:
            candidates_list_new.append(cluster[0]["candidate"])
        else:
            names = [c["candidate"]["org_name"] for c in cluster]
            name_merged = " + ".join(names)

            candidates = [can["candidate"] for can in cluster]
            can = geo_distance_calculator.get_stdev_coordinates(candidates)[1]
            can["org_name"] = name_merged
            candidates_list_new.append(can)

    return candidates_list_new


def generate_initail_landmarks(sample_list):
    '''
    generate initial landmarks from sample list; initial landmarks are chosen from samples who have only one candidate
    :param sample_list:
    :return: a dict from ip to coordinates
    '''
    dict_landmarks = {}
    for sample in sample_list:
        if sample["status"] == enumeration.SAMPLE_STATUS_FIN:
            dict_landmarks[sample["ip"]] = sample["coordinate"]
        else:
            pass
    return dict_landmarks


def match_guard_to_candidates(sample, dict_landmarks, max_distance):
    '''
    :param sample:
    :param dict_landmarks: existing landmarks
    :param max_distance:
    :return: a new sample with guards to its candidates
    '''
    if sample["status"] != enumeration.SAMPLE_STATUS_WFVG:
        return sample

    candidates = sample["candidates_merged"]
    dict_potential_guards = {}

    # find all potential guards in maximal distance to each candidate
    for can in candidates:
        can["guard"] = {"dis": 9999999999, "guard": None}
        for key, val in dict_landmarks.items():
            dis = geo_distance_calculator.get_geodistance_btw_2coordinates(can["longitude"], can["latitude"], val["longitude"], val["latitude"])
            if dis <= max_distance:
                dict_potential_guards[key] = val

    # match guard to its corresponding candidate
    for key, val in dict_potential_guards.items():
        # find the closest candidates
        min_dis = 9999999999
        closest_can = None
        for can in candidates:
            dis = geo_distance_calculator.get_geodistance_btw_2coordinates(can["longitude"], can["latitude"], val["longitude"], val["latitude"])
            if dis < min_dis:
                min_dis = dis
                closest_can = can

        # check whether this landmark is the closest one, if it is the one, it is the guard of this candidate
        if min_dis < closest_can["guard"]["dis"]:
            closest_can["guard"]["dis"] = min_dis
            closest_can["guard"]["guard"] = {"ip": key, "org_name": val["org_name"], "longitude": val["longitude"], "latitude": val["latitude"]}

    # check if there is any failed match
    # if there is a single candidate without a guard, the target's location is not ready to inferred
    guards = []
    for can in candidates:
        if can["guard"]["dis"] == 9999999999:
            sample["status"] = enumeration.SAMPLE_STATUS_WFVG
            return sample
        guards.append(can["guard"]["guard"])

    # if the stickiness between each pair of guards is too high(dis < max_distance),
    # the target's location is not ready to inferred
    for pair in combinations(guards, 2):
        dis = geo_distance_calculator.get_geodistance_btw_2coordinates(pair[0]["longitude"], pair[0]["latitude"], pair[1]["longitude"], pair[1]["latitude"])
        if dis < max_distance:
            sample["status"] = enumeration.SAMPLE_STATUS_WFVG
            return sample

    # otherwise, ready to be inferred
    sample["status"] = enumeration.SAMPLE_STATUS_RTBI
    return sample


def get_indirect_route(tracert_list1, tracert_list2):
    '''
    :param tracert_list1: [{"ip": 6.6.6.6, "delay": 784.4}, ...]
    :param tracert_list2:
    :return:
    '''
    tracert_list1.reverse()
    tracert_list2.reverse()

    for ind1, h1 in enumerate(tracert_list1):
        for ind2, h2 in enumerate(tracert_list2):
            if h1["ip"] == "256.256.256.256" or h2["ip"] == "256.256.256.256":
                continue
            if h1["ip"] == h2["ip"]:
                p1 = ind1
                p2 = ind2

                rt_piece1 = tracert_list1[:p1]
                rt_piece2 = tracert_list2[:p2]
                rt_piece2.reverse()

                direct_rt_list = rt_piece1 + rt_piece2
                delay_indirect = 0
                for hop in direct_rt_list:
                    if hop["ip"] == "256.256.256.256":
                        continue
                    delay_indirect += hop["delay"]
                return delay_indirect

# def generate_landmarks(sample_list):
#     '''
#     select an exact location for each IP and return a landmark
#     :param sample_list:
#     :return: landmark: a dict from IP to coordinate
#     '''
#     huge_num = 99999999999
#     dict_landmark = {}
#
#     for info in sample_list:
#         ip = info["ip"]
#         try:
#             lat_com = info["result_fr_commercial_tool"]["latitude"]
#             lng_com = info["result_fr_commercial_tool"]["longitude"]
#             candidates_fr_registration_db = info["result_fr_registration_db"]["candidates"]
#             query_registration_db = info["result_fr_registration_db"]["query"]
#             candidates_fr_page = info["result_fr_page"]["candidates"]
#             query_page = info["result_fr_page"]["query"]
#             ipinfo_fr_commercial_tools = info["result_fr_commercial_tool"]
#         except KeyError:
#             continue
#
#         dis_registration_db2ipip = geo_distance_calculator.get_geodistance_btw_2coordinates(lng_com, lat_com, candidates_fr_registration_db[0]["longitude"],
#                                                                                   candidates_fr_registration_db[0]["latitude"]) if candidates_fr_registration_db and len(
#             candidates_fr_registration_db) == 1 else huge_num
#         dis_pageinfo2ipip = geo_distance_calculator.get_geodistance_btw_2coordinates(lng_com, lat_com, candidates_fr_page[0]["longitude"],
#                                                                                      candidates_fr_page[0]["latitude"]) if candidates_fr_page and len(
#             candidates_fr_page) == 1 else huge_num
#         dis_page2registration_db = geo_distance_calculator.get_geodistance_btw_2coordinates(candidates_fr_registration_db[0]["longitude"], candidates_fr_registration_db[0]["latitude"],
#                                                                                   candidates_fr_page[0]["longitude"], candidates_fr_page[0]["latitude"]) \
#             if candidates_fr_page and len(candidates_fr_page) == 1 and candidates_fr_registration_db and len(candidates_fr_registration_db) == 1 else huge_num
#
#         # show result
#         output = {
#             "ip": ip,
#             "coordinate_fr_commercial_tools": {
#                 "longitude": ipinfo_fr_commercial_tools["longitude"],
#                 "latitude": ipinfo_fr_commercial_tools["latitude"]
#             },
#             "registration_db": {
#                 "query": query_registration_db,
#                 "coordinate": candidates_fr_registration_db,
#                 "dis_registration_db2com": dis_registration_db2ipip,
#             },
#             "page": {
#                 "query": query_page,
#                 "coordinate": candidates_fr_page,
#                 "dis_page2com": dis_pageinfo2ipip,
#             },
#             "dis_pageinfo2registration_db": dis_page2registration_db,
#         }
#         # logger.war(json.dumps(output, indent=2))
#
#         threshold = 20000
#         if dis_registration_db2ipip <= threshold or dis_pageinfo2ipip <= threshold:
#             lng = None
#             lat = None
#             if dis_pageinfo2ipip < dis_registration_db2ipip:
#                 lng = candidates_fr_page[0]["longitude"]
#                 lat = candidates_fr_page[0]["latitude"]
#             else:
#                 lng = candidates_fr_registration_db[0]["longitude"]
#                 lat = candidates_fr_registration_db[0]["latitude"]
#             dict_landmark[ip] = [lng, lat]
#     return dict_landmark


if __name__ == "__main__":
    # locations = [{"org_name": "1", 'longitude': -122.270001, 'latitude': 37.8055388}, {"org_name": "2", 'longitude': -87.858491, 'latitude': 37.8055388},
    #              {"org_name": "3", 'longitude': -122.270001, 'latitude': 37.8055388},
    #              {"org_name": "4", 'longitude': -87.858491, 'latitude': 41.87776059999999}, ]
    # print(merge_near_candidates(locations, 200000))

    rt1 = [{"ip": "12."}]
    pass







