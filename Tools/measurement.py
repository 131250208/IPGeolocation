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
    api = "https://atlas.ripe.net:443/api/v2/measurements/%s?key=%s" % (measurement_id, settings.KEY_RIPE)
    res = requests.delete(api)
    print(res.text)


def delete_measurement_by_tag(tag):
    api = "https://atlas.ripe.net:443/api/v2/measurements/my-tags/%s/stop?key=%s" % (tag, settings.KEY_RIPE)
    res = requests.post(api)
    print(res.text)


def measure_by_ripe_hugenum(map_account2key, list_target, list_probes, start, days, interval, tag):
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
    days2stamp = 86400.0 * days
    measurement_chunks = chunks(list_target, 100)
    size = len(measurement_chunks)
    assert size <= len(map_account2key.keys())

    for ind, mc in enumerate(measurement_chunks):
        interval_ = interval + 0.0
        start_time = start + math.ceil(interval_ / size) * ind
        stop_time = start_time + days2stamp
        res = measure_by_ripe(mc, list_probes, start_time, stop_time, interval, tag)
        print(res.status_code)
        print(res.text)


def measure_by_ripe(account, key, list_target, list_probes, start_time, stop_time, interval, tag):
    '''
    start measurements on targets
    :param list_target:
    :return:
    '''
    list_measurement = []
    for t in list_target:
        list_measurement.append({
            "is_public ": True,
            "description": "Traceroute measurement to %s" % t,
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
            "tags": tag,
            "interval": interval,
        })
    api = "https://atlas.ripe.net:443/api/v2/measurements/traceroute?key=%s" % key
    data = {
        "bill_to": account,
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

if __name__ == "__main__":
    delete_measurement_by_tag("ip-geolocation-train-dataset")
    # import pytz
    # tz = pytz.timezone('America/New_York')
    # start_time = datetime.datetime.now(tz).timestamp() + 120
    #
    # map_ip_coordination = json.load(open("../resources/landmarks_ripe_us.json", "r"))
    # list_target = [k for k in map_ip_coordination.keys() if k is not None]
    # probes = ["35151", "13191", "33713", "34726", "14750", "10693"]  # 6
    # # start_time = datetime.datetime(2018, 10, 28, 7, 50, 0).timestamp()
    # measure_by_ripe_hugenum(list_target, probes, start_time, 1, 21600, ["ip-geolocation-train-dataset",])


