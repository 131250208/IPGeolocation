from math import radians, cos, sin, asin, sqrt
from Tools import mylogger
logger = mylogger.Logger("../Log/geo_distance_calculator.py.log")
from itertools import combinations
import pyprind
import numpy as np


def get_geodistance_btw_2coordinates(lng1, lat1, lng2, lat2):
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


def get_stdev_coordinates(coordinates):
    '''
    get expected coordinate and stdev during several coordinates
    :param coordinates:
    :return:
    '''
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
        dis += get_geodistance_btw_2coordinates(co["longitude"], co["latitude"], exp_lng, exp_lat)
    return dis / len(coordinates), {"longitude": exp_lng, "latitude": exp_lat}


def merge_near_locations(locations_list, max_distance):
    len_locations = len(locations_list)
    if len_locations <= 1:
        return locations_list

    clusters_list = [{"index": ind, "cluster": [{"index": ind, "location": c}, ], } for ind, c in enumerate(locations_list)]

    dis_locations = list(np.zeros([len_locations, len_locations], dtype=float).tolist())
    pair_list = combinations(clusters_list, 2)
    for pair in pair_list:
        c1 = pair[0]["cluster"][0]
        c2 = pair[1]["cluster"][0]
        dis = get_geodistance_btw_2coordinates(c1["location"]["longitude"], c1["location"]["latitude"],
                                                                 c2["location"]["longitude"], c2["location"]["latitude"])
        dis_locations[c1["index"]][c2["index"]] = dis

    dis_clusters = dis_locations[:]

    while True:
        # print("-----cluster and merge near locations..., len_clusters: %d---------" % len(clusters_list))
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
        for i in range(len_locations):
            new_dis = dis_locations[ind_1][i] if dis_locations[ind_1][i] > dis_locations[ind_2][i] else dis_locations[ind_2][i]
            dis_clusters[ind_1][i] = new_dis
            dis_clusters[i][ind_1] = new_dis

    locations_list_new = []
    for cluster in clusters_list:
        cluster = cluster["cluster"]
        if len(cluster) == 1:
            locations_list_new.append(cluster[0]["location"])
        else:
            locations = [can["location"] for can in cluster]
            can = get_stdev_coordinates(locations)[1]
            locations_list_new.append(can)

    return locations_list_new


if __name__ == "__main__":
    # print(get_geodistance_btw_2coordinates(-161.90583, 19.50139, -161.75583, 19.50139))
    
    locations = [{"name": "1", 'longitude': -122.270001, 'latitude': 37.8055388}, {"name": "2", 'longitude': -87.858491, 'latitude': 37.8055388},
                 {"name": "3", 'longitude': -122.270001, 'latitude': 37.8255388}, {"name": "4", 'longitude': -87.858491, 'latitude': 41.87776059999999},]
    print(merge_near_locations(locations, 2000000))
    pass






