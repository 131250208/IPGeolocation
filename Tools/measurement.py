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
            "packet_interval": 2,
            "size": 48,
            "target": t,
            "tags": tags,
            "include_probe_id": False,
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


def get_measurement_res_by_tag(tag):
    api = "https://atlas.ripe.net:443/api/v2/measurements/?tags=%s&key=%s" % (tag, settings.RIPE_KEY_O)

    url = api
    dict_target2mfrprbs = {}
    while True:
        res = rt.try_best_request_get(url, 5, get_measurement_res_by_tag)
        measurement = json.loads(res.text)
        results = measurement["results"]

        for dst in pyprind.prog_bar(results):
            target = dst["target"]
            res_dst = rt.try_best_request_get(dst["result"], 5, get_measurement_res_by_tag)
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


def measure_process(dict_target2mfrprbs):
    for target_ip in dict_target2mfrprbs.keys():
        dict_prb2trac = dict_target2mfrprbs[target_ip]
        for pb_ip in dict_prb2trac.keys():
            list_hops = dict_prb2trac[pb_ip]
            # delay_total = 0
            for hp in list_hops:
                vec = get_vect(hp["rtts"])
                hp["vec"] = vec
                # delay_total += vec[1] # add the best
            # dict_prb2trac[pb_ip] = {
            #     "list_hops": list_hops,
            #     "delay_total": delay_total
            # }
    return dict_target2mfrprbs

if __name__ == "__main__":
    import pytz
    tz = pytz.timezone('America/New_York')
    start_time = datetime.datetime.now(tz).timestamp() + 120

    map_ip_coordination = json.load(open("../resources/landmarks_ripe_us.json", "r"))
    list_target = [k for k in map_ip_coordination.keys() if k is not None]
    # probes = ["35151", "13191", "33713", "34726", "14750", "10693"]  # 6
    probes_50 = json.load(open("../resources/probes_us.json", "r"))
    probes = list(probes_50.values())
    measure_by_ripe_hugenum_oneoff_ping(list_target, probes, start_time, ["ipg-2018110602", ],
                                        "measured by 50 probes, would be used to do contrast experiment")


