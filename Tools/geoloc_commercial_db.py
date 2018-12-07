import geoip2.database
from geoip2.errors import AddressNotFoundError
from Tools.IPLocate import IPplus360
from Tools import settings, requests_tools as rt, geo_distance_calculator
import json
import datx
import requests

reader_geolite2 = geoip2.database.Reader('../Sources/GeoLite2-City.mmdb')
reader_ipip = datx.City(settings.IP_INFO_IPIP_PATH)
reader_ipplus = IPplus360()
reader_ipplus.load_dat("../Sources/IP_trial_2018M11_single_WGS84.dat")


def ip_geolocation_geolite2(ip):
    try:
        res = reader_geolite2.city(ip)
    except AddressNotFoundError:
        return None

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
    result = reader_ipplus.locate_ip(ip)
    return {
        "continent": result[2],
        "country": result[5],
        "region": result[6],
        "city": result[7],
        "longitude": float(result[9]) if result[9] != "" else None,
        "latitude": float(result[10]) if result[10] != "" else None,
    }


def get_locations_info_by_commercial_tools(ip):
    ipinfo_fr_ipplus = ip_geolocation_ipplus360(ip)  # free trial, one month expire, low precision
    ipinfo_fr_ipip = ip_geolocation_ipip(ip)
    ipinfo_fr_geolite2 = ip_geolocation_geolite2(ip)  # free, low precision

    return {
            "ipplus": {
                "coarse_grained_region": "%s, %s, %s" %
                                         (ipinfo_fr_ipplus["country"], ipinfo_fr_ipplus["region"],
                                          ipinfo_fr_ipplus["city"]),
                "longitude": ipinfo_fr_ipplus["longitude"],
                "latitude": ipinfo_fr_ipplus["latitude"]},
            "ipip": {
                "coarse_grained_region": "%s, %s, %s" %
                                         (ipinfo_fr_ipip["country"], ipinfo_fr_ipip["region"],
                                          ipinfo_fr_ipip["city"]),
                "longitude": ipinfo_fr_ipip["longitude"],
                "latitude": ipinfo_fr_ipip["latitude"]},
            "geolite2": {
                "coarse_grained_region": "%s, %s, %s" %
                                         (ipinfo_fr_geolite2["country"], ipinfo_fr_geolite2["region"],
                                          ipinfo_fr_geolite2["city"]),
                "longitude": ipinfo_fr_geolite2["longitude"],
                "latitude": ipinfo_fr_geolite2["latitude"], },
            }


def get_location_info_by_commercial_tools_unanimous(ip):
    ipinfo_fr_ipplus = ip_geolocation_ipplus360(ip)  # free trial, one month expire, low precision
    ipinfo_fr_ipip = ip_geolocation_ipip(ip)
    ipinfo_fr_geolite2 = ip_geolocation_geolite2(ip)  # free, low precision

    if ipinfo_fr_ipip is None or ipinfo_fr_ipplus is None or ipinfo_fr_geolite2 is None:
        return None

    if ipinfo_fr_geolite2["city"] == ipinfo_fr_ipplus["city"] and ipinfo_fr_geolite2["city"] == ipinfo_fr_ipip["city"] and\
            ipinfo_fr_ipplus["city"] != "":
        coordinates = [{"longitude": ipinfo_fr_ipplus["longitude"],
                        "latitude": ipinfo_fr_ipplus["latitude"]},
                       {"longitude": ipinfo_fr_ipip["longitude"],
                        "latitude": ipinfo_fr_ipip["latitude"]},
                       {"longitude": ipinfo_fr_geolite2["longitude"],
                        "latitude": ipinfo_fr_geolite2["latitude"]},
                       ]
        stdev, exp_coordinate = geo_distance_calculator.get_stdev_coordinates(coordinates)

        return {"coarse_grained_region": "%s, %s, %s" %
                                         (ipinfo_fr_geolite2["country"], ipinfo_fr_geolite2["region"], ipinfo_fr_geolite2["city"]),
                "country": ipinfo_fr_ipip["country"],
                "stdev": stdev,
                "longitude": exp_coordinate["longitude"],
                "latitude": exp_coordinate["latitude"],
                "coordinates": {
                    "ipplus": {
                        "coarse_grained_region": "%s, %s, %s" %
                                                 (ipinfo_fr_ipplus["country"], ipinfo_fr_ipplus["region"],
                                                  ipinfo_fr_ipplus["city"]),
                        "longitude": ipinfo_fr_ipplus["longitude"],
                        "latitude": ipinfo_fr_ipplus["latitude"]},
                    "ipip": {
                        "coarse_grained_region": "%s, %s, %s" %
                                                 (ipinfo_fr_ipip["country"], ipinfo_fr_ipip["region"],
                                                  ipinfo_fr_ipip["city"]),
                        "longitude": ipinfo_fr_ipip["longitude"],
                        "latitude": ipinfo_fr_ipip["latitude"]},
                    "geolite2": {
                        "coarse_grained_region": "%s, %s, %s" %
                                                 (ipinfo_fr_geolite2["country"], ipinfo_fr_geolite2["region"],
                                                  ipinfo_fr_geolite2["city"]),
                        "longitude": ipinfo_fr_geolite2["longitude"],
                        "latitude": ipinfo_fr_geolite2["latitude"],},
                    },
                }

    return None

