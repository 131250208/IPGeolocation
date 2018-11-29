from math import radians, cos, sin, asin, sqrt
from Tools import mylogger
logger = mylogger.Logger("../Log/geo_distance_calculator.py.log")


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


if __name__ == "__main__":
    coordinates = [{"longitude": -122.0236615, "latitude": 37.4092265},
                   {"longitude": -122.0144237, "latitude": 37.4160916},
                   {"longitude": -121.8942373, "latitude": 37.3801141},
                   ]
    print(get_stdev_coordinates(coordinates))
    pass






