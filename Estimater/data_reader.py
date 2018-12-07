import pytz
import datetime
import json
from Tools import network_measurer
import numpy as np
from Tools import settings


def get_vect(list_rtt):
    if len(list_rtt) == 0:
        return None

    list_valid_rtt = []
    loss = 0

    for rtt in list_rtt:
        if rtt != -1:
            list_valid_rtt.append(rtt)
        else:
            loss += 1

    if loss == len(list_rtt):
        return [-1, -1, -1, -1, -1]

    array = np.array(list_valid_rtt)
    best = array.min()
    worst = array.max()
    avg = array.mean()
    stdev = array.std()

    return [loss, best, worst, avg, stdev]


def construct_vec(dict_target2mfrprbs):
    for target_ip in dict_target2mfrprbs.keys():
        dict_prb2trac = dict_target2mfrprbs[target_ip]["measurement"]
        for pb_ip in dict_prb2trac.keys():
            list_hops = dict_prb2trac[pb_ip]
            for hp in list_hops:
                vec = get_vect(hp["rtts"])
                hp["vec"] = vec

    return dict_target2mfrprbs


def preprocess_measurement_data(account, measurement_tag):
    ripe = network_measurer.RipeAtlas(account["account"], account["key"])
    measurement_data = ripe.get_traceroute_measurement_by_tag(measurement_tag) # dict: target ip 2 measurement data
    # add vectors
    measurement_data = construct_vec(measurement_data)
    # add coordinates
    dict_target2coord = json.load(open("../Sources/landmarks_ripe_us.json", "r"))
    for key in measurement_data.keys():
        measurement_data[key]["coordinate"] = {
            "longitude": dict_target2coord[key]["longitude"],
            "latitude": dict_target2coord[key]["latitude"],
        }

    return measurement_data


def check_measurement_data(measurement):
    count = 0
    for val in measurement.values():
        measurement_probes = val["measurement"].values()
        num_probe = len(measurement_probes)
        work = False
        for p in measurement_probes:
            vec = p[0]["vec"]
            if vec is not None and len(vec) == 5:
                work = True
        if work:
            count += 1
    return count


if __name__ == "__main__":
    # measurement_data = preprocess_measurement_data(settings.RIPE_ACCOUNT_KEY[1], "ipg-22018111701")
    # json.dump(measurement_data, open("../Sources/measurement_ipg-22018111701.json", "w"))
    # print(measurement_data)

    list_pid = ["34759", "33759", "21031", "25224", "24899", "15760", "24908", "32462", "24971", "24633", "35561",
                "10599", "30352", "11634", "35620", "35415", "12180", "2427", "16951", "12105", "30263", "35001",
                "26946", "24247"]

    measurement = json.load(open("../Sources/measurement_ipg-22018111601.json", "r"))
    count = 0
    # print(list(measurement.values())[0].keys())
    unstable_pid_set = set()
    for v in measurement.values():
        de_pid_list = v["measurement"].keys()
        num_p = len(list(de_pid_list))
        if num_p != 24:
            for p in list_pid:
                if p not in de_pid_list:
                    unstable_pid_set.add(p)
            count += 1
    print(count)
    print(unstable_pid_set)

    count_suc = check_measurement_data(measurement)
    print(count_suc)

