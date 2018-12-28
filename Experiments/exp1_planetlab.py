import json
import strings, enumeration
from Tools import geo_distance_calculator, geoloc_commercial_db
from LandmarksCollector import data_preprocessor as dp_lmc
import settings
import numpy as np
import pyprind

def map_ip_2_geolocation_st_1():
    samples = json.load(open("../Sources/experiments/samples_planetlab_us_0.1.json", "r", encoding="utf-8"))
    # org_name_dict = json.load(open("../Sources/org_names/org_name_dict_index/org_name_dict_index_0.json", "r"))
    # samples = dp_lmc.extract_org_names(samples, org_name_dict)
    # samples = dp_lmc.incorporate_coarse_locations_fr_commercial_dbs(samples)
    # samples = dp_lmc.incorporate_candidates_fr_web_mapping_services(samples, settings.RADIUS_FOR_SEARCHING_CANDIDATES)
    samples = dp_lmc.merge_near_candidates(samples)
    return samples


if __name__ == "__main__":
    # samples = json.load(open("../Sources/experiments/samples_planetlab_us.json", "r", encoding="utf-8"))
    # for s in pyprind.prog_bar(samples):
    #     ip = s["ip"]
    #     est_ipip = geoloc_commercial_db.ip_geolocation_ipip(ip)
    #     est_ipplus = geoloc_commercial_db.ip_geolocation_ipplus360(ip)
    #     est_ipinfo = geoloc_commercial_db.ip_geolocation_ipinfo(ip)
    #     est_geolite2 = geoloc_commercial_db.ip_geolocation_geolite2(ip)
    #     est_ipstack = geoloc_commercial_db.ip_geolocation_ipstack(ip)
    #
    #     s["est_ipip"] = est_ipip
    #     s["est_ipplus"] = est_ipplus
    #     s["est_ipinfo"] = est_ipinfo
    #     s["est_geolite2"] = est_geolite2
    #     s["est_ipstack"] = est_ipstack
    # json.dump(samples, open("../Sources/experiments/samples_planetlab_us.json", "w", encoding="utf-8"))


    samples = json.load(open("../Sources/experiments/samples_planetlab_us.json", "r", encoding="utf-8"))
    count = 0
    sample_fin = []
    med_list_one = []
    med_list_ipplus = []
    med_list_ipinfo = []
    med_list_ipip = []
    med_list_ipstack = []
    med_list_geolite2 = []
    for sample in samples:
        if sample[strings.KEY_STATUS] == enumeration.SAMPLE_STATUS_FIN:
            # if sample["dis_coarse_2_ground"] > 50000:
            #     continue
            ground_lon = sample["longitude"]
            ground_lat = sample["latitude"]
            lon_one = sample[strings.KEY_ESTIMATED_COORDINATE]["longitude"]
            lat_one = sample[strings.KEY_ESTIMATED_COORDINATE]["latitude"]
            lon_ipplus = sample["est_ipplus"]["longitude"]
            lat_ipplus = sample["est_ipplus"]["latitude"]
            lon_ipip = sample["est_ipip"]["longitude"]
            lat_ipip = sample["est_ipip"]["latitude"]
            lon_ipinfo = sample["est_ipinfo"]["longitude"]
            lat_ipinfo = sample["est_ipinfo"]["latitude"]
            lon_ipstack = sample["est_ipstack"]["longitude"]
            lat_ipstack = sample["est_ipstack"]["latitude"]
            lon_geolite2 = sample["est_geolite2"]["longitude"]
            lat_geolite2 = sample["est_geolite2"]["latitude"]
            err_one = geo_distance_calculator.get_geodistance_btw_2coordinates(ground_lon, ground_lat, lon_one, lat_one)
            err_ipplus = geo_distance_calculator.get_geodistance_btw_2coordinates(ground_lon, ground_lat, lon_ipplus, lat_ipplus)
            err_ipip = geo_distance_calculator.get_geodistance_btw_2coordinates(ground_lon, ground_lat, lon_ipip, lat_ipip)
            err_ipinfo = geo_distance_calculator.get_geodistance_btw_2coordinates(ground_lon, ground_lat, lon_ipinfo, lat_ipinfo)
            err_geolite2 = geo_distance_calculator.get_geodistance_btw_2coordinates(ground_lon, ground_lat, lon_geolite2, lat_geolite2)
            err_ipstack = geo_distance_calculator.get_geodistance_btw_2coordinates(ground_lon, ground_lat, lon_ipstack, lat_ipstack)

            sample_fin.append(sample)
            count += 1
            med_list_one.append(err_one)
            med_list_ipplus.append(err_ipplus)
            med_list_ipip.append(err_ipip)
            med_list_ipstack.append(err_ipstack)
            med_list_ipinfo.append(err_ipinfo)
            med_list_geolite2.append(err_geolite2)

            print("ip: {}, org: {} \n"
                  "error_one: {:.1f}, err_ipplus: {:.1f}, err_ipip: {:.1f}, err_ipinfo: {:.1f}, err_ipstack: {:.1f}, err_geolite2: {:.1f}".format(sample["ip"], sample["organization"], err_one, err_ipplus, err_ipip, err_ipinfo, err_ipstack, err_geolite2))
    print(np.median(med_list_one))
    print(len(sample_fin))

    # import numpy as np
    # import matplotlib.pyplot as plt
    # samples = []
    # for ind, e in enumerate(med_list_one):
    #     if e > 18000:
    #         continue
    #     samples.append(e)
    #
    # arr = samples
    # plt.plot(np.sort(arr), np.linspace(0, 1, len(arr), endpoint=False), color="red")
    # plt.show()