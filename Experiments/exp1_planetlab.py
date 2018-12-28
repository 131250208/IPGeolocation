import json
import strings, enumeration
from Tools import geo_distance_calculator, geoloc_commercial_db
from LandmarksCollector import data_preprocessor as dp_lmc
import settings
import numpy as np


def map_ip_2_geolocation_st_1():
    samples = json.load(open("../Sources/experiments/samples_planetlab_us_0.1.json", "r", encoding="utf-8"))
    # org_name_dict = json.load(open("../Sources/org_names/org_name_dict_index/org_name_dict_index_0.json", "r"))
    # samples = dp_lmc.extract_org_names(samples, org_name_dict)
    # samples = dp_lmc.incorporate_coarse_locations_fr_commercial_dbs(samples)
    # samples = dp_lmc.incorporate_candidates_fr_web_mapping_services(samples, settings.RADIUS_FOR_SEARCHING_CANDIDATES)
    samples = dp_lmc.merge_near_candidates(samples)
    return samples


if __name__ == "__main__":
    samples = json.load(open("../Sources/experiments/samples_planetlab_us.json", "r", encoding="utf-8"))
    count = 0
    sample_fin = []
    error_list = []
    for sample in samples:
        if sample[strings.KEY_STATUS] == enumeration.SAMPLE_STATUS_FIN:
            # if sample["dis_coarse_2_ground"] > 50000:
            #     continue
            med_one = geo_distance_calculator.get_geodistance_btw_2coordinates(sample["longitude"], sample["latitude"], sample[strings.KEY_ESTIMATED_COORDINATE]["longitude"], sample[strings.KEY_ESTIMATED_COORDINATE]["latitude"])

            sample_fin.append(sample)
            count += 1
            error_list.append(med_one)

            print("ip: {}, org: {} error_dis: {}".format(sample["ip"], sample["organization"], med_one))
    print(np.median(error_list))
    print(len(sample_fin))

    import numpy as np
    import matplotlib.pyplot as plt
    samples = []
    for ind, e in enumerate(error_list):
        if e > 18000:
            continue
        samples.append(e)

    arr = samples
    plt.plot(np.sort(arr), np.linspace(0, 1, len(arr), endpoint=False), color="red")
    plt.show()