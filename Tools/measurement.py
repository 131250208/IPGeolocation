from Tools import requests_tools as rt
import requests
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import time
from Tools import settings
import json
import datetime
import math
import pyprind
from urllib import parse
import numpy as np

def init_chrome():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % settings.PROXY_ABROAD)
    chrome_options.add_argument("--headless")
    prefs = {'profile.managed_default_content_settings.images': 2}
    chrome_options.add_experimental_option('prefs', prefs)
    chrome = webdriver.Chrome(options=chrome_options)
    return chrome


def wait_to_get_element(driver, css_selector):
    while True:
        try:
            element = WebDriverWait(driver, settings.DRIVER_WAITING_TIME).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
            break
        except Exception as e:
            print(e)
            continue
    return element


def extract_trace_route_info_fr_text(res_trace_route_text):
    date = None
    day = None
    time = None
    search_group = re.search("Start: (\d{4}-\d{1,2}-\d{1,2})(\w+)(\d{2}:\d{2}:\d{2})\+0000", res_trace_route_text)
    if search_group:
        date = search_group.group(1)
        day = search_group.group(2)
        time = search_group.group(3)

    res_trace_route = []
    iter = re.finditer(
        "\d+\.\|-- (\d+\.\d+\.\d+\.\d+)[\s\t]+(\d+\.\d%)[\s\t]+(\d)[\s\t]+(\d\.\d)[\s\t]+(\d\.\d)[\s\t]+(\d\.\d)[\s\t]+(\d\.\d)[\s\t]+(\d\.\d)",
        res_trace_route_text)
    for match in iter:
        res_trace_route.append({
            "ip": match.group(1),
            "loss": match.group(2),
            "snt": match.group(3),
            "Last": match.group(4),
            "Avg": match.group(5),
            "Best": match.group(6),
            "Wrst": match.group(7),
            "StDev": match.group(8),
        })

    return {
        "date": date,
        "day": day,
        "time": time,
        "route_info": res_trace_route
    }


def trace_route_query(chrome, hostname):
    input_hostname = wait_to_get_element(chrome, "input#hostname")
    input_hostname.clear()
    input_hostname.send_keys(hostname)
    btn_trace = wait_to_get_element(chrome, "button#traceBtn:enabled")
    btn_trace.click()
    wait_to_get_element(chrome, "button#traceBtn:enabled")
    defr = wait_to_get_element(chrome, "div#traceResultdefr > pre").text

    usny = wait_to_get_element(chrome, "div#traceResultusny > pre").text
    usmi = wait_to_get_element(chrome, "div#traceResultusmi > pre").text
    usda = wait_to_get_element(chrome, "div#traceResultusda > pre").text
    ussf = wait_to_get_element(chrome, "div#traceResultussf > pre").text
    usse = wait_to_get_element(chrome, "div#traceResultusse > pre").text

    cato = wait_to_get_element(chrome, "div#traceResultcato > pre").text
    uklo = wait_to_get_element(chrome, "div#traceResultuklo > pre").text
    frpa = wait_to_get_element(chrome, "div#traceResultfrpa > pre").text
    nlam = wait_to_get_element(chrome, "div#traceResultnlam > pre").text
    sgsg = wait_to_get_element(chrome, "div#traceResultsgsg > pre").text
    ausy = wait_to_get_element(chrome, "div#traceResultausy > pre").text
    jptk = wait_to_get_element(chrome, "div#traceResultjptk > pre").text
    inba = wait_to_get_element(chrome, "div#traceResultinba > pre").text


    res_dict = {
        "defr": extract_trace_route_info_fr_text(defr),
        "usny": extract_trace_route_info_fr_text(usny),
        "usmi": extract_trace_route_info_fr_text(usmi),
        "usda": extract_trace_route_info_fr_text(usda),
        "ussf": extract_trace_route_info_fr_text(ussf),
        "usse": extract_trace_route_info_fr_text(usse),
        "cato": extract_trace_route_info_fr_text(cato),
        "uklo": extract_trace_route_info_fr_text(uklo),
        "frpa": extract_trace_route_info_fr_text(frpa),
        "nlam": extract_trace_route_info_fr_text(nlam),
        "sgsg": extract_trace_route_info_fr_text(sgsg),
        "ausy": extract_trace_route_info_fr_text(ausy),
        "jptk": extract_trace_route_info_fr_text(jptk),
        "inba": extract_trace_route_info_fr_text(inba),
            }
    return json.dumps(res_dict)


def measure_by_keycdn():
    chrome = init_chrome()
    chrome.get("https://tools.keycdn.com/traceroute")

    json_landmarks = json.load(open("../resources/landmarks_planet_lab_us.json", "r"))
    for lm in pyprind.prog_bar(json_landmarks):
        ip = lm["ip"]
        t1 = time.time()
        res = trace_route_query(chrome, ip)
        lm["measurement_keycdn"] = [res, ]
        print(res)
        t2 = time.time()
        print(t2 - t1)

    json.dump(json_landmarks, open("../resources/landmarks_planetlab_us_measured.json", "w"))

# -------------------------------------------------------------------------------------------------------------------------------------------


def chunks(arr, n):
    '''
    split arr into chunks whose size is n
    :param arr:
    :param n:
    :return:
    '''
    return [arr[i:i + n] for i in range(0, len(arr), n)]


def chunks_avg(arr, m):
    '''
    split the arr into m chunks
    :param arr:
    :param m:
    :return:
    '''
    n = int(math.ceil(len(arr) / float(m)))
    return [arr[i:i + n] for i in range(0, len(arr), n)]


def delete_measurement(measurement_id):
    api = "https://atlas.ripe.net:443/api/v2/measurements/%s?key=%s" % (measurement_id, settings.RIPE_KEY_O)
    res = requests.delete(api)
    print(res.text)


def quote(queryStr):
    try:
        queryStr = parse.quote(queryStr)
    except:
        queryStr = parse.quote(queryStr.encode('utf-8', 'ignore'))

    return queryStr


def delete_measurement_by_tag(tag):
    tag = quote(tag)
    api = "https://atlas.ripe.net:443/api/v2/measurements/my-tags/%s/stop?key=%s" % (tag, settings.RIPE_KEY_O)
    data = {"tag": tag}
    res = requests.post(api, data=json.dumps(data))
    print(res.text)


def measure_by_ripe_hugenum_oneoff_traceroute(list_target, list_probes, start, tags, des):
    list_target = [ip for ip in list_target if ip not in list_probes]
    measurement_chunks = chunks(list_target, 100)

    for ind, mc in enumerate(measurement_chunks):
        start_time = start + 1800.0 * ind
        res = measure_by_ripe_oneoff_traceroute(mc, list_probes, start_time, tags, des)
        print(res.status_code)
        print(res.text)


def measure_by_ripe_hugenum_scheduled_traceroute(list_target, list_probes, start, days, interval, tags, des):
    '''
    split a huge measurement to small chunks
    :param list_target:
    :param list_probes:
    :param start:
    :param days:
    :param interval:
    :param tag:
    :return:
    '''
    list_target = [ip for ip in list_target if ip not in list_probes]
    days2stamp = 86400.0 * days
    measurement_chunks = chunks(list_target, 100)
    size = len(measurement_chunks)
    # assert size <= len(map_account2key.keys())

    for ind, mc in enumerate(measurement_chunks):
        interval_ = interval + 0.0
        start_time = start + math.ceil(interval_ / size) * ind
        stop_time = start_time + days2stamp
        res = measure_by_ripe_scheduled_traceroute(mc, list_probes, start_time, stop_time, interval, tags, des)
        print(res.status_code)
        print(res.text)


def measure_by_ripe_hugenum_oneoff_ping(list_target, list_probes, start, tags, des):
    list_target = [ip for ip in list_target if ip not in list_probes]
    measurement_chunks = chunks(list_target, 100)

    for ind, mc in enumerate(measurement_chunks):
        start_time = start + 300 + 1200.0 * ind
        res = measure_by_ripe_oneoff_ping(mc, list_probes, start_time, tags, des)
        print(res.status_code)
        print(res.text)


def measure_by_ripe_oneoff_ping(list_target, list_probes, start_time, tags, des):
    list_measurement = []
    for t in list_target:
        list_measurement.append({
            "is_public ": True,
            "description": "Ping measurement to %s, %s" % (t, des),
            "af": 4,
            "type": "ping",
            "packets": 4,
            "packet_interval": 2000,
            "size": 48,
            "target": t,
            "tags": tags,
            "include_probe_id": True,
        })
    api = "https://atlas.ripe.net:443/api/v2/measurements/ping?key=%s" % settings.RIPE_KEY_O
    data = {
        "bill_to": "wychengpublic@163.com",
        "is_oneoff": True,
        "start_time": start_time,
        "definitions": list_measurement,
        "probes": [{
            "requested": len(list_probes),
            "type": "probes",
            "value": ",".join(list_probes),
        }]
    }

    res = requests.post(api, data=json.dumps(data), headers=rt.get_random_headers())
    return res


def measure_by_ripe_oneoff_traceroute(list_target, list_probes, start_time, tags, des):
    list_measurement = []
    for t in list_target:
        list_measurement.append({
            "is_public ": True,
            "description": "Traceroute measurement to %s, %s" % (t, des),
            "af": 4,
            "type": "traceroute",
            "packets": 4,
            "first_hop": 1,
            "max_hops": 32,
            "paris": 16,
            "size": 48,
            "protocol": "ICMP",
            "duplicate_timeout": 4000,
            "hop_by_hop_option_size": 0,
            "destination_option_size": 0,
            "dont_fragment": False,
            "target": t,
            "tags": tags,
        })
    api = "https://atlas.ripe.net:443/api/v2/measurements/traceroute?key=%s" % settings.RIPE_KEY_O
    data = {
        "bill_to": "wychengpublic@163.com",
        "is_oneoff": True,
        "start_time": start_time,
        "definitions": list_measurement,
        "probes": [{
            "requested": len(list_probes),
            "type": "probes",
            "value": ",".join(list_probes),
        }]
    }

    res = requests.post(api, data=json.dumps(data), headers=rt.get_random_headers())
    return res


def measure_by_ripe_scheduled_traceroute(list_target, list_probes, start_time, stop_time, interval, tags, des):
    '''
    start measurements on targets
    :param list_target:
    :return:
    '''
    list_measurement = []
    for t in list_target:
        list_measurement.append({
            "is_public ": True,
            "description": "Traceroute measurement to %s, %s" % (t, des),
            "af": 4,
            "type": "traceroute",
            "packets": 4,
            "first_hop": 1,
            "max_hops": 32,
            "paris": 16,
            "size": 48,
            "protocol": "ICMP",
            "duplicate_timeout": 4000,
            "hop_by_hop_option_size": 0,
            "destination_option_size": 0,
            "dont_fragment": False,
            "target": t,
            "tags": tags,
            "interval": interval,
        })
    api = "https://atlas.ripe.net:443/api/v2/measurements/traceroute?key=%s" % settings.RIPE_KEY_O
    data = {
        "bill_to": "wychengpublic@163.com",
        "is_oneoff": False,
        "start_time": start_time,
        "stop_time": stop_time,
        # "skip_dns_check": True,
        "definitions": list_measurement,
        "probes": [{
            "requested": len(list_probes),
            "type": "probes",
            "value": ",".join(list_probes),
        }]
    }

    res = requests.post(api, data=json.dumps(data), headers=rt.get_random_headers())
    return res


def get_ping_measurement_by_tag(tag):
    api = "https://atlas.ripe.net:443/api/v2/measurements/?tags=%s&key=%s" % (tag, settings.RIPE_KEY_O)

    url = api
    dict_target2mfrprbs = {}
    while True:
        res = rt.try_best_request_get(url, 5, "get_traceroute_measurement_by_tag")
        measurement = json.loads(res.text)
        results = measurement["results"]

        for dst in pyprind.prog_bar(results):
            target = dst["target"]
            res_dst = rt.try_best_request_get(dst["result"], 5, "get_traceroute_measurement_by_tag")
            measurement_per_dst = json.loads(res_dst.text)

            dict_prb2trac = {}
            for prb in measurement_per_dst:
                prb_id = prb["prb_id"]
                prb_res = prb["result"]


def get_traceroute_measurement_by_tag(tag):
    api = "https://atlas.ripe.net:443/api/v2/measurements/?tags=%s&key=%s" % (tag, settings.RIPE_KEY_O)

    url = api
    dict_target2mfrprbs = {}
    while True:
        res = rt.try_best_request_get(url, 5, "get_traceroute_measurement_by_tag")
        measurement = json.loads(res.text)
        results = measurement["results"]

        for dst in pyprind.prog_bar(results):
            target = dst["target"]
            res_dst = rt.try_best_request_get(dst["result"], 5, "get_traceroute_measurement_by_tag")
            measurement_per_dst = json.loads(res_dst.text)

            dict_prb2trac = {}
            for prb in measurement_per_dst:
                prb_id = prb["prb_id"]
                prb_res = prb["result"]
                list_res = []
                for res in prb_res:
                    pk_hop = res["result"]
                    rtts = []
                    addr_rt = None
                    for pk in pk_hop:
                        if "x" in pk:
                            rtt = -1
                            rtts.append(rtt)
                        if "rtt" in pk:
                            rtt = pk["rtt"]
                            rtts.append(rtt)

                        if "from" in pk:
                            addr_rt = pk["from"]

                    list_res.append({
                        "hop": res["hop"],
                        "addr_rt": addr_rt,
                        "rtts": rtts,
                    })
                dict_prb2trac[prb_id] = list_res

            dict_target2mfrprbs[target] = dict_prb2trac

        next_page = measurement["next"]
        if next_page is None:
            break
        url = next_page

    return dict_target2mfrprbs


def get_probe_info(pid):
    api = "https://atlas.ripe.net:443/api/v2/probes/%s?key=%s" % (pid, settings.RIPE_KEY_O)
    res = rt.try_best_request_get(api, 5, "get_probe_info")
    json_res = json.loads(res.text)
    ip = json_res["address_v4"]
    lng = json_res["geometry"]["coordinates"][0]
    lat = json_res["geometry"]["coordinates"][1]
    return {
        "ip": ip, "longitude": lng, "latitude": lat,
    }


def get_inp_4_baidu_map(list_pid):
    map_pid2coordinate = {}
    list_name_value = []
    for pid in list_pid:
        probe_info = get_probe_info(pid)
        map_pid2coordinate[pid] = [probe_info["longitude"], probe_info["latitude"]]
        list_name_value.append({"name": pid, "value": 50})

    print(list_name_value)
    print("---------------------------------")
    print(map_pid2coordinate)


if __name__ == "__main__":
    pass
    # import random
    # m = {'4894': [-84.3185, 33.8495], '3588': [-147.1185, 64.8615], '12100': [-112.0725, 33.4475], '6373': [-94.5795, 39.0985], '13191': [-122.1085, 37.3875], '33713': [-104.9925, 39.9085], '13334': [-72.6915, 41.7695], '34719': [-75.7525, 39.6815], '14750': [-81.8805, 26.6375], '10099': [-84.4085, 33.9615], '14606': [-156.0225, 20.7805], '31492': [-91.6385, 41.8485], '32462': [-113.7895, 42.4985], '12156': [-89.5305, 40.9005], '10406': [-86.9825, 40.2005], '10507': [-97.8225, 37.7505], '33316': [-84.5825, 37.8805], '13397': [-91.0885, 30.3605], '31128': [-70.6815, 44.2015], '32710': [-77.6125, 38.2075], '34297': [-72.5185, 42.3705], '33068': [-83.9495, 43.4215], '34710': [-92.1025, 46.7875], '34723': [-88.2715, 34.8185], '14244': [-93.8505, 38.5895], '19957': [-112.0305, 46.6005], '27310': [-96.0725, 41.1275], '32849': [-119.7205, 39.0415], '13288': [-71.7385, 43.6415], '12012': [-74.5725, 39.9885], '35066': [-106.2195, 35.8205], '15740': [-75.9005, 42.5375], '11795': [-78.8785, 35.8595], '25224': [-96.8115, 46.8195], '32186': [-82.5085, 40.3305], '34313': [-97.6425, 35.5585], '33262': [-123.1095, 44.6385], '10598': [-78.0185, 40.7915], '33065': [-71.4495, 41.4495], '35293': [-81.0685, 33.9885], '15723': [-97.1115, 44.8985], '12180': [-86.9385, 36.0575], '35620': [-101.8615, 33.5775], '19976': [-111.6895, 40.2805], '10693': [-72.9685, 43.5685], '33609': [-79.2625, 37.3915], '35151': [-119.5505, 47.3175], '12726': [-81.5615, 38.3705], '34726': [-88.3115, 44.2305], '12159': [-108.7605, 44.7515]}
    # list_pid = list(json.load(open("../resources/probes_us_25.json", "r")).values())
    # # list_pid = list(m.keys())
    # random.seed(time.time())
    # random.shuffle(list_pid)
    # map_pid2co = {}
    # list_pid2val = []
    # for pid in list_pid:
    #     list_pid2val.append({"name": pid, "value": 50})
    #     map_pid2co[pid] = m[pid]
    # print(len(list_pid2val))
    # print(list_pid2val)
    # print("----------------")
    # print(map_pid2co)



