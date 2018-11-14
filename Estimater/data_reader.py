import pytz
import datetime
import json
from Tools import measurement
import numpy as np


def measure_targets():

    tz = pytz.timezone('America/New_York')

    start_time = datetime.datetime.now(tz).timestamp() + 120

    map_ip_coordination = json.load(open("../resources/landmarks_ripe_us.json", "r"))
    list_target = [k for k in map_ip_coordination.keys() if k is not None]
    # probes = ["35151", "13191", "", "34726", "14750", "10693"]  # 6
    probes = json.load(open("../resources/probes_us_25.json", "r"))
    probes = list(probes.values())
    measurement.measure_by_ripe_hugenum_oneoff_traceroute(list_target, probes, start_time, ["ipg-2018111001", ],
                                        "measured by 25 probes, would be used to do contrast experiment")


def get_vect(list_rtt):
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
        dict_prb2trac = dict_target2mfrprbs[target_ip]
        for pb_ip in dict_prb2trac.keys():
            list_hops = dict_prb2trac[pb_ip]
            for hp in list_hops:
                vec = get_vect(hp["rtts"])
                hp["vec"] = vec

    return dict_target2mfrprbs


def preprocess_measurement_data(measurement_tag):
    measurement_data = measurement.get_traceroute_measurement_by_tag(measurement_tag) # dict: target ip 2 measurement data
    # add vectors
    measurement_data = construct_vec(measurement_data)
    # add coordinates
    dict_target2coord = json.load(open("../resources/landmarks_ripe_us.json", "r"))
    for key in measurement_data.keys():
        measurement_data[key]["coordinate"] = {
            "longitude": dict_target2coord[0],
            "latitude": dict_target2coord[1],
        }

    return measurement_data


if __name__ == "__main__":
    pass