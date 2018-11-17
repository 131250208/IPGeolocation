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

class KeyCDN:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % settings.PROXY_ABROAD)
        chrome_options.add_argument("--headless")
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option('prefs', prefs)
        self.chrome = webdriver.Chrome(options=chrome_options)
        
    def wait_to_get_element(self, driver, css_selector):
        while True:
            try:
                element = WebDriverWait(driver, settings.DRIVER_WAITING_TIME).until(
                    ec.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
                break
            except Exception as e:
                print(e)
                continue
        return element
    
    def extract_trace_route_info_fr_text(self, res_trace_route_text):
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
    
    def trace_route_query(self, chrome, hostname):
        input_hostname = self.wait_to_get_element(chrome, "input#hostname")
        input_hostname.clear()
        input_hostname.send_keys(hostname)
        btn_trace = self.wait_to_get_element(chrome, "button#traceBtn:enabled")
        btn_trace.click()
        self.wait_to_get_element(chrome, "button#traceBtn:enabled")
        defr = self.wait_to_get_element(chrome, "div#traceResultdefr > pre").text
    
        usny = self.wait_to_get_element(chrome, "div#traceResultusny > pre").text
        usmi = self.wait_to_get_element(chrome, "div#traceResultusmi > pre").text
        usda = self.wait_to_get_element(chrome, "div#traceResultusda > pre").text
        ussf = self.wait_to_get_element(chrome, "div#traceResultussf > pre").text
        usse = self.wait_to_get_element(chrome, "div#traceResultusse > pre").text
    
        cato = self.wait_to_get_element(chrome, "div#traceResultcato > pre").text
        uklo = self.wait_to_get_element(chrome, "div#traceResultuklo > pre").text
        frpa = self.wait_to_get_element(chrome, "div#traceResultfrpa > pre").text
        nlam = self.wait_to_get_element(chrome, "div#traceResultnlam > pre").text
        sgsg = self.wait_to_get_element(chrome, "div#traceResultsgsg > pre").text
        ausy = self.wait_to_get_element(chrome, "div#traceResultausy > pre").text
        jptk = self.wait_to_get_element(chrome, "div#traceResultjptk > pre").text
        inba = self.wait_to_get_element(chrome, "div#traceResultinba > pre").text
    
    
        res_dict = {
            "defr": self.extract_trace_route_info_fr_text(defr),
            "usny": self.extract_trace_route_info_fr_text(usny),
            "usmi": self.extract_trace_route_info_fr_text(usmi),
            "usda": self.extract_trace_route_info_fr_text(usda),
            "ussf": self.extract_trace_route_info_fr_text(ussf),
            "usse": self.extract_trace_route_info_fr_text(usse),
            "cato": self.extract_trace_route_info_fr_text(cato),
            "uklo": self.extract_trace_route_info_fr_text(uklo),
            "frpa": self.extract_trace_route_info_fr_text(frpa),
            "nlam": self.extract_trace_route_info_fr_text(nlam),
            "sgsg": self.extract_trace_route_info_fr_text(sgsg),
            "ausy": self.extract_trace_route_info_fr_text(ausy),
            "jptk": self.extract_trace_route_info_fr_text(jptk),
            "inba": self.extract_trace_route_info_fr_text(inba),
                }
        return json.dumps(res_dict)
    
    def measure_by_keycdn(self):
        self.chrome.get("https://tools.keycdn.com/traceroute")
    
        json_landmarks = json.load(open("../Sources/landmarks_planet_lab_us.json", "r"))
        for lm in pyprind.prog_bar(json_landmarks):
            ip = lm["ip"]
            t1 = time.time()
            res = self.trace_route_query(self.chrome, ip)
            lm["measurement_keycdn"] = [res, ]
            print(res)
            t2 = time.time()
            print(t2 - t1)
    
        json.dump(json_landmarks, open("../Sources/landmarks_planetlab_us_measured.json", "w"))

# -------------------------------------------------------------------------------------------------------------------------------------------


class RipeAtlas:    
    def __init__(self, account=None, key=None):
        self.account = account
        self.key = key
        
    def chunks(self, arr, n):
        '''
        split arr into chunks whose size is n
        :param arr:
        :param n:
        :return:
        '''
        return [arr[i:i + n] for i in range(0, len(arr), n)]

    def chunks_avg(self, arr, m):
        '''
        split the arr into m chunks
        :param arr:
        :param m:
        :return:
        '''
        n = int(math.ceil(len(arr) / float(m)))
        return [arr[i:i + n] for i in range(0, len(arr), n)]

    def delete_measurement(self, measurement_id):
        api = "https://atlas.ripe.net:443/api/v2/measurements/%s?key=%s" % (measurement_id, self.key)
        res = requests.delete(api)
        print(res.text)

    def quote(self, queryStr):
        try:
            queryStr = parse.quote(queryStr)
        except:
            queryStr = parse.quote(queryStr.encode('utf-8', 'ignore'))
        return queryStr

    def delete_measurement_by_tag(self, tag):
        tag = self.quote(tag)
        api = "https://atlas.ripe.net:443/api/v2/measurements/my-tags/%s/stop?key=%s" % (tag, self.key)
        data = {"tag": tag}
        res = requests.post(api, data=json.dumps(data))
        print(res.text)

    def measure_by_ripe_hugenum_oneoff_traceroute(self, list_target, list_probes, start, tags, des):
        list_target = [ip for ip in list_target if ip not in list_probes]
        measurement_chunks = self.chunks(list_target, 100)
    
        for ind, mc in enumerate(measurement_chunks):
            start_time = start + 900.0 * ind
            res = self.measure_by_ripe_oneoff_traceroute(mc, list_probes, start_time, tags, des)
            print(res.status_code)
            print(res.text)

    def measure_by_ripe_hugenum_scheduled_traceroute(self, list_target, list_probes, start, days, interval, tags, des):
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
        measurement_chunks = self.chunks(list_target, 100)
        size = len(measurement_chunks)
        # assert size <= len(map_account2key.keys())
    
        for ind, mc in enumerate(measurement_chunks):
            interval_ = interval + 0.0
            start_time = start + math.ceil(interval_ / size) * ind
            stop_time = start_time + days2stamp
            res = self.measure_by_ripe_scheduled_traceroute(mc, list_probes, start_time, stop_time, interval, tags, des)
            print(res.status_code)
            print(res.text)

    def measure_by_ripe_hugenum_oneoff_ping(self, list_target, list_probes, start, tags, des):
        list_target = [ip for ip in list_target if ip not in list_probes]
        measurement_chunks = self.chunks(list_target, 100)
    
        for ind, mc in enumerate(measurement_chunks):
            start_time = start + 300 + 1200.0 * ind
            res = self.measure_by_ripe_oneoff_ping(mc, list_probes, start_time, tags, des)
            print(res.status_code)
            print(res.text)

    def measure_by_ripe_oneoff_ping(self, list_target, list_probes, start_time, tags, des):
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
        api = "https://atlas.ripe.net:443/api/v2/measurements/ping?key=%s" % self.key
        data = {
            "bill_to": self.account,
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

    def measure_by_ripe_oneoff_traceroute(self, list_target, list_probes, start_time, tags, des):
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
        api = "https://atlas.ripe.net:443/api/v2/measurements/traceroute?key=%s" % self.key
        data = {
            "bill_to": self.account,
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

    def measure_by_ripe_scheduled_traceroute(self, list_target, list_probes, start_time, stop_time, interval, tags, des):
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
        api = "https://atlas.ripe.net:443/api/v2/measurements/traceroute?key=%s" % self.key
        data = {
            "bill_to": self.account,
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

    def get_ping_measurement_by_tag(self, tag):
        api = "https://atlas.ripe.net:443/api/v2/measurements/?tags=%s&key=%s" % (tag, self.key)
    
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

    def get_traceroute_measurement_by_tag(self, tag):
        api = "https://atlas.ripe.net:443/api/v2/measurements/?tags=%s&key=%s" % (tag, self.key)
    
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

# ------------------------------------------------------------------------------------------
#   no need for key
    def get_probe_info(self, pid):
        '''
        :param pid: type: str, id of a probe
        :return: 
        '''
        api = "https://atlas.ripe.net:443/api/v2/probes/%s?key=%s" % (pid, settings.RIPE_KEY_O)
        res = rt.try_best_request_get(api, 5, "get_probe_info")
        json_res = json.loads(res.text)
        ip = json_res["address_v4"]
        lng = json_res["geometry"]["coordinates"][0]
        lat = json_res["geometry"]["coordinates"][1]
        return {
            "ip": ip, "longitude": lng, "latitude": lat,
        }

    def get_all_probes_us(self, path=None):
        if path is not None:
            try:
                all_probes = json.load(open(path, "r", encoding="utf-8"))
                assert all_probes is not None
                return all_probes
            except Exception as e:
                pass
    
        map_ip_coordinate = {}
        map_id_coordinate = {}
        data = []
    
        url = "https://atlas.ripe.net:443/api/v2/probes/?country_code=US&status=1"
    
        while True:
            res = requests.get(url)
            print("req: %s" % url)
            probes = json.loads(res.text)
    
            for r in probes["results"]:
                ip = r["address_v4"]
                if ip is None:
                    continue
                id = r["id"]
    
                if id is not None:
                    coordinates = r["geometry"]["coordinates"]
                    map_id_coordinate[id] = coordinates  # [lon, lat]
                    map_ip_coordinate[ip] = {
                        "longitude": coordinates[0],
                        "latitude": coordinates[1],
                    }
                    data.append({"name": id, "value": 50})
    
            next_page = probes["next"]
            if next_page is None:
                break
            else:
                url = next_page
    
        print(json.dumps(map_id_coordinate))
        print("-------------------------")
        print(json.dumps(data))
        return map_ip_coordinate
    
    
    # 24
    # [{'name': '34759', 'value': 50}, {'name': '33759', 'value': 50}, {'name': '21031', 'value': 50}, {'name': '25224', 'value': 50}, {'name': '24899', 'value': 50}, {'name': '28255', 'value': 50}, {'name': '24908', 'value': 50}, {'name': '32462', 'value': 50}, {'name': '24971', 'value': 50}, {'name': '24633', 'value': 50}, {'name': '19960', 'value': 50}, {'name': '29383', 'value': 50}, {'name': '30352', 'value': 50}, {'name': '11634', 'value': 50}, {'name': '35620', 'value': 50}, {'name': '35415', 'value': 50}, {'name': '13266', 'value': 50}, {'name': '12146', 'value': 50}, {'name': '16951', 'value': 50}, {'name': '12105', 'value': 50}, {'name': '30263', 'value': 50}, {'name': '35001', 'value': 50}, {'name': '24994', 'value': 50}, {'name': '14750', 'value': 50}]
    # {'34759': [-122.0505, 47.5415], '33759': [-116.5705, 47.3215], '21031': [-108.5815, 45.7975], '25224': [-96.8115, 46.8195], '24899': [-84.7785, 45.0415], '28255': [-71.3705, 42.9395], '24908': [-124.4225, 43.0515], '32462': [-113.7895, 42.4985], '24971': [-105.2195, 39.7475], '24633': [-95.8415, 41.2585], '19960': [-86.1595, 39.7675], '29383': [-77.1885, 39.2585], '30352': [-121.9605, 37.2385], '11634': [-113.6215, 37.1195], '35620': [-101.8615, 33.5775], '35415': [-95.9425, 36.1495], '13266': [-86.5595, 34.7405], '12146': [-82.0405, 34.7405], '16951': [-118.0205, 33.7075], '12105': [-110.7525, 32.0795], '30263': [-99.4795, 27.5285], '35001': [-93.2025, 30.1975], '24994': [-90.0685, 29.9495], '14750': [-81.8805, 26.6375]}
    
    # all
    # [{"name": 24, "value": 50}, {"name": 28, "value": 50}, {"name": 32, "value": 50}, {"name": 75, "value": 50}, {"name": 85, "value": 50}, {"name": 97, "value": 50}, {"name": 125, "value": 50}, {"name": 131, "value": 50}, {"name": 146, "value": 50}, {"name": 190, "value": 50}, {"name": 202, "value": 50}, {"name": 319, "value": 50}, {"name": 331, "value": 50}, {"name": 345, "value": 50}, {"name": 394, "value": 50}, {"name": 468, "value": 50}, {"name": 591, "value": 50}, {"name": 801, "value": 50}, {"name": 1053, "value": 50}, {"name": 1058, "value": 50}, {"name": 1101, "value": 50}, {"name": 1105, "value": 50}, {"name": 1107, "value": 50}, {"name": 1113, "value": 50}, {"name": 1119, "value": 50}, {"name": 1121, "value": 50}, {"name": 1123, "value": 50}, {"name": 1127, "value": 50}, {"name": 1131, "value": 50}, {"name": 1132, "value": 50}, {"name": 1133, "value": 50}, {"name": 1134, "value": 50}, {"name": 1136, "value": 50}, {"name": 1145, "value": 50}, {"name": 1149, "value": 50}, {"name": 1160, "value": 50}, {"name": 1163, "value": 50}, {"name": 1169, "value": 50}, {"name": 1171, "value": 50}, {"name": 1179, "value": 50}, {"name": 1184, "value": 50}, {"name": 1185, "value": 50}, {"name": 1186, "value": 50}, {"name": 1188, "value": 50}, {"name": 1189, "value": 50}, {"name": 1194, "value": 50}, {"name": 1196, "value": 50}, {"name": 1198, "value": 50}, {"name": 1408, "value": 50}, {"name": 2285, "value": 50}, {"name": 2289, "value": 50}, {"name": 2427, "value": 50}, {"name": 2529, "value": 50}, {"name": 2549, "value": 50}, {"name": 2591, "value": 50}, {"name": 2592, "value": 50}, {"name": 2627, "value": 50}, {"name": 2685, "value": 50}, {"name": 2711, "value": 50}, {"name": 2858, "value": 50}, {"name": 3041, "value": 50}, {"name": 3103, "value": 50}, {"name": 3218, "value": 50}, {"name": 3252, "value": 50}, {"name": 3280, "value": 50}, {"name": 3410, "value": 50}, {"name": 3423, "value": 50}, {"name": 3483, "value": 50}, {"name": 3517, "value": 50}, {"name": 3524, "value": 50}, {"name": 3525, "value": 50}, {"name": 3574, "value": 50}, {"name": 3579, "value": 50}, {"name": 3588, "value": 50}, {"name": 3600, "value": 50}, {"name": 3620, "value": 50}, {"name": 3640, "value": 50}, {"name": 3644, "value": 50}, {"name": 3645, "value": 50}, {"name": 3649, "value": 50}, {"name": 3650, "value": 50}, {"name": 3651, "value": 50}, {"name": 3656, "value": 50}, {"name": 3658, "value": 50}, {"name": 3660, "value": 50}, {"name": 3663, "value": 50}, {"name": 3666, "value": 50}, {"name": 3669, "value": 50}, {"name": 3670, "value": 50}, {"name": 3671, "value": 50}, {"name": 3673, "value": 50}, {"name": 3683, "value": 50}, {"name": 3685, "value": 50}, {"name": 3686, "value": 50}, {"name": 3715, "value": 50}, {"name": 3724, "value": 50}, {"name": 3737, "value": 50}, {"name": 3753, "value": 50}, {"name": 3756, "value": 50}, {"name": 3767, "value": 50}, {"name": 3964, "value": 50}, {"name": 4019, "value": 50}, {"name": 4069, "value": 50}, {"name": 4085, "value": 50}, {"name": 4111, "value": 50}, {"name": 4148, "value": 50}, {"name": 4155, "value": 50}, {"name": 4279, "value": 50}, {"name": 4304, "value": 50}, {"name": 4307, "value": 50}, {"name": 4334, "value": 50}, {"name": 4405, "value": 50}, {"name": 4412, "value": 50}, {"name": 4417, "value": 50}, {"name": 4549, "value": 50}, {"name": 4551, "value": 50}, {"name": 4602, "value": 50}, {"name": 4674, "value": 50}, {"name": 4706, "value": 50}, {"name": 4894, "value": 50}, {"name": 4930, "value": 50}, {"name": 4958, "value": 50}, {"name": 4959, "value": 50}, {"name": 4969, "value": 50}, {"name": 4981, "value": 50}, {"name": 6045, "value": 50}, {"name": 6061, "value": 50}, {"name": 6062, "value": 50}, {"name": 6065, "value": 50}, {"name": 6066, "value": 50}, {"name": 6067, "value": 50}, {"name": 6072, "value": 50}, {"name": 6074, "value": 50}, {"name": 6080, "value": 50}, {"name": 6092, "value": 50}, {"name": 6093, "value": 50}, {"name": 6095, "value": 50}, {"name": 6097, "value": 50}, {"name": 6101, "value": 50}, {"name": 6125, "value": 50}, {"name": 6130, "value": 50}, {"name": 6140, "value": 50}, {"name": 6144, "value": 50}, {"name": 6147, "value": 50}, {"name": 6155, "value": 50}, {"name": 6156, "value": 50}, {"name": 6201, "value": 50}, {"name": 6208, "value": 50}, {"name": 6216, "value": 50}, {"name": 6222, "value": 50}, {"name": 6223, "value": 50}, {"name": 6229, "value": 50}, {"name": 6231, "value": 50}, {"name": 6236, "value": 50}, {"name": 6247, "value": 50}, {"name": 6257, "value": 50}, {"name": 6259, "value": 50}, {"name": 6264, "value": 50}, {"name": 6265, "value": 50}, {"name": 6266, "value": 50}, {"name": 6274, "value": 50}, {"name": 6280, "value": 50}, {"name": 6285, "value": 50}, {"name": 6286, "value": 50}, {"name": 6287, "value": 50}, {"name": 6288, "value": 50}, {"name": 6289, "value": 50}, {"name": 6290, "value": 50}, {"name": 6292, "value": 50}, {"name": 6341, "value": 50}, {"name": 6343, "value": 50}, {"name": 6355, "value": 50}, {"name": 6373, "value": 50}, {"name": 6379, "value": 50}, {"name": 6388, "value": 50}, {"name": 6389, "value": 50}, {"name": 6394, "value": 50}, {"name": 6407, "value": 50}, {"name": 6408, "value": 50}, {"name": 6409, "value": 50}, {"name": 6411, "value": 50}, {"name": 10007, "value": 50}, {"name": 10009, "value": 50}, {"name": 10099, "value": 50}, {"name": 10185, "value": 50}, {"name": 10194, "value": 50}, {"name": 10204, "value": 50}, {"name": 10284, "value": 50}, {"name": 10286, "value": 50}, {"name": 10301, "value": 50}, {"name": 10303, "value": 50}, {"name": 10305, "value": 50}, {"name": 10312, "value": 50}, {"name": 10317, "value": 50}, {"name": 10322, "value": 50}, {"name": 10329, "value": 50}, {"name": 10331, "value": 50}, {"name": 10333, "value": 50}, {"name": 10334, "value": 50}, {"name": 10335, "value": 50}, {"name": 10338, "value": 50}, {"name": 10342, "value": 50}, {"name": 10343, "value": 50}, {"name": 10350, "value": 50}, {"name": 10355, "value": 50}, {"name": 10356, "value": 50}, {"name": 10357, "value": 50}, {"name": 10360, "value": 50}, {"name": 10362, "value": 50}, {"name": 10369, "value": 50}, {"name": 10371, "value": 50}, {"name": 10377, "value": 50}, {"name": 10381, "value": 50}, {"name": 10386, "value": 50}, {"name": 10390, "value": 50}, {"name": 10394, "value": 50}, {"name": 10399, "value": 50}, {"name": 10400, "value": 50}, {"name": 10402, "value": 50}, {"name": 10403, "value": 50}, {"name": 10406, "value": 50}, {"name": 10413, "value": 50}, {"name": 10415, "value": 50}, {"name": 10418, "value": 50}, {"name": 10423, "value": 50}, {"name": 10427, "value": 50}, {"name": 10443, "value": 50}, {"name": 10445, "value": 50}, {"name": 10456, "value": 50}, {"name": 10457, "value": 50}, {"name": 10458, "value": 50}, {"name": 10462, "value": 50}, {"name": 10465, "value": 50}, {"name": 10473, "value": 50}, {"name": 10478, "value": 50}, {"name": 10482, "value": 50}, {"name": 10484, "value": 50}, {"name": 10486, "value": 50}, {"name": 10491, "value": 50}, {"name": 10495, "value": 50}, {"name": 10498, "value": 50}, {"name": 10506, "value": 50}, {"name": 10507, "value": 50}, {"name": 10515, "value": 50}, {"name": 10518, "value": 50}, {"name": 10540, "value": 50}, {"name": 10542, "value": 50}, {"name": 10543, "value": 50}, {"name": 10544, "value": 50}, {"name": 10545, "value": 50}, {"name": 10551, "value": 50}, {"name": 10553, "value": 50}, {"name": 10555, "value": 50}, {"name": 10556, "value": 50}, {"name": 10562, "value": 50}, {"name": 10564, "value": 50}, {"name": 10565, "value": 50}, {"name": 10568, "value": 50}, {"name": 10576, "value": 50}, {"name": 10584, "value": 50}, {"name": 10587, "value": 50}, {"name": 10595, "value": 50}, {"name": 10597, "value": 50}, {"name": 10598, "value": 50}, {"name": 10599, "value": 50}, {"name": 10626, "value": 50}, {"name": 10637, "value": 50}, {"name": 10640, "value": 50}, {"name": 10657, "value": 50}, {"name": 10668, "value": 50}, {"name": 10674, "value": 50}, {"name": 10675, "value": 50}, {"name": 10677, "value": 50}, {"name": 10692, "value": 50}, {"name": 10693, "value": 50}, {"name": 10694, "value": 50}, {"name": 10704, "value": 50}, {"name": 10727, "value": 50}, {"name": 10743, "value": 50}, {"name": 10751, "value": 50}, {"name": 10790, "value": 50}, {"name": 10814, "value": 50}, {"name": 10884, "value": 50}, {"name": 10905, "value": 50}, {"name": 11010, "value": 50}, {"name": 11018, "value": 50}, {"name": 11090, "value": 50}, {"name": 11171, "value": 50}, {"name": 11203, "value": 50}, {"name": 11207, "value": 50}, {"name": 11215, "value": 50}, {"name": 11500, "value": 50}, {"name": 11513, "value": 50}, {"name": 11528, "value": 50}, {"name": 11529, "value": 50}, {"name": 11536, "value": 50}, {"name": 11550, "value": 50}, {"name": 11582, "value": 50}, {"name": 11634, "value": 50}, {"name": 11689, "value": 50}, {"name": 11705, "value": 50}, {"name": 11747, "value": 50}, {"name": 11765, "value": 50}, {"name": 11795, "value": 50}, {"name": 11797, "value": 50}, {"name": 11801, "value": 50}, {"name": 11857, "value": 50}, {"name": 11911, "value": 50}, {"name": 11985, "value": 50}, {"name": 11989, "value": 50}, {"name": 12012, "value": 50}, {"name": 12016, "value": 50}, {"name": 12030, "value": 50}, {"name": 12060, "value": 50}, {"name": 12070, "value": 50}, {"name": 12100, "value": 50}, {"name": 12103, "value": 50}, {"name": 12105, "value": 50}, {"name": 12108, "value": 50}, {"name": 12115, "value": 50}, {"name": 12116, "value": 50}, {"name": 12121, "value": 50}, {"name": 12134, "value": 50}, {"name": 12144, "value": 50}, {"name": 12146, "value": 50}, {"name": 12154, "value": 50}, {"name": 12156, "value": 50}, {"name": 12159, "value": 50}, {"name": 12161, "value": 50}, {"name": 12166, "value": 50}, {"name": 12180, "value": 50}, {"name": 12215, "value": 50}, {"name": 12226, "value": 50}, {"name": 12297, "value": 50}, {"name": 12300, "value": 50}, {"name": 12303, "value": 50}, {"name": 12315, "value": 50}, {"name": 12316, "value": 50}, {"name": 12318, "value": 50}, {"name": 12320, "value": 50}, {"name": 12330, "value": 50}, {"name": 12331, "value": 50}, {"name": 12380, "value": 50}, {"name": 12402, "value": 50}, {"name": 12426, "value": 50}, {"name": 12443, "value": 50}, {"name": 12452, "value": 50}, {"name": 12459, "value": 50}, {"name": 12475, "value": 50}, {"name": 12504, "value": 50}, {"name": 12506, "value": 50}, {"name": 12518, "value": 50}, {"name": 12548, "value": 50}, {"name": 12563, "value": 50}, {"name": 12578, "value": 50}, {"name": 12579, "value": 50}, {"name": 12588, "value": 50}, {"name": 12600, "value": 50}, {"name": 12611, "value": 50}, {"name": 12621, "value": 50}, {"name": 12622, "value": 50}, {"name": 12623, "value": 50}, {"name": 12650, "value": 50}, {"name": 12652, "value": 50}, {"name": 12668, "value": 50}, {"name": 12671, "value": 50}, {"name": 12673, "value": 50}, {"name": 12681, "value": 50}, {"name": 12685, "value": 50}, {"name": 12686, "value": 50}, {"name": 12688, "value": 50}, {"name": 12691, "value": 50}, {"name": 12692, "value": 50}, {"name": 12693, "value": 50}, {"name": 12695, "value": 50}, {"name": 12710, "value": 50}, {"name": 12726, "value": 50}, {"name": 12728, "value": 50}, {"name": 12739, "value": 50}, {"name": 12768, "value": 50}, {"name": 12788, "value": 50}, {"name": 12842, "value": 50}, {"name": 12853, "value": 50}, {"name": 12863, "value": 50}, {"name": 12879, "value": 50}, {"name": 12908, "value": 50}, {"name": 12920, "value": 50}, {"name": 12925, "value": 50}, {"name": 12938, "value": 50}, {"name": 12984, "value": 50}, {"name": 12999, "value": 50}, {"name": 13004, "value": 50}, {"name": 13056, "value": 50}, {"name": 13070, "value": 50}, {"name": 13109, "value": 50}, {"name": 13120, "value": 50}, {"name": 13128, "value": 50}, {"name": 13131, "value": 50}, {"name": 13146, "value": 50}, {"name": 13159, "value": 50}, {"name": 13191, "value": 50}, {"name": 13205, "value": 50}, {"name": 13222, "value": 50}, {"name": 13249, "value": 50}, {"name": 13253, "value": 50}, {"name": 13266, "value": 50}, {"name": 13283, "value": 50}, {"name": 13288, "value": 50}, {"name": 13311, "value": 50}, {"name": 13318, "value": 50}, {"name": 13334, "value": 50}, {"name": 13396, "value": 50}, {"name": 13397, "value": 50}, {"name": 13499, "value": 50}, {"name": 13514, "value": 50}, {"name": 13520, "value": 50}, {"name": 13528, "value": 50}, {"name": 13547, "value": 50}, {"name": 13551, "value": 50}, {"name": 13561, "value": 50}, {"name": 13565, "value": 50}, {"name": 13572, "value": 50}, {"name": 13585, "value": 50}, {"name": 13614, "value": 50}, {"name": 13639, "value": 50}, {"name": 13651, "value": 50}, {"name": 13654, "value": 50}, {"name": 13666, "value": 50}, {"name": 13671, "value": 50}, {"name": 13673, "value": 50}, {"name": 13676, "value": 50}, {"name": 13681, "value": 50}, {"name": 13688, "value": 50}, {"name": 13694, "value": 50}, {"name": 13735, "value": 50}, {"name": 13826, "value": 50}, {"name": 13831, "value": 50}, {"name": 13834, "value": 50}, {"name": 13838, "value": 50}, {"name": 13864, "value": 50}, {"name": 13942, "value": 50}, {"name": 13960, "value": 50}, {"name": 14053, "value": 50}, {"name": 14064, "value": 50}, {"name": 14066, "value": 50}, {"name": 14069, "value": 50}, {"name": 14071, "value": 50}, {"name": 14090, "value": 50}, {"name": 14102, "value": 50}, {"name": 14114, "value": 50}, {"name": 14132, "value": 50}, {"name": 14164, "value": 50}, {"name": 14166, "value": 50}, {"name": 14226, "value": 50}, {"name": 14227, "value": 50}, {"name": 14233, "value": 50}, {"name": 14237, "value": 50}, {"name": 14242, "value": 50}, {"name": 14244, "value": 50}, {"name": 14300, "value": 50}, {"name": 14324, "value": 50}, {"name": 14337, "value": 50}, {"name": 14340, "value": 50}, {"name": 14546, "value": 50}, {"name": 14578, "value": 50}, {"name": 14583, "value": 50}, {"name": 14604, "value": 50}, {"name": 14606, "value": 50}, {"name": 14720, "value": 50}, {"name": 14748, "value": 50}, {"name": 14750, "value": 50}, {"name": 14777, "value": 50}, {"name": 14795, "value": 50}, {"name": 14796, "value": 50}, {"name": 14881, "value": 50}, {"name": 14882, "value": 50}, {"name": 14981, "value": 50}, {"name": 15015, "value": 50}, {"name": 15035, "value": 50}, {"name": 15038, "value": 50}, {"name": 15039, "value": 50}, {"name": 15086, "value": 50}, {"name": 15133, "value": 50}, {"name": 15145, "value": 50}, {"name": 15387, "value": 50}, {"name": 15542, "value": 50}, {"name": 15605, "value": 50}, {"name": 15619, "value": 50}, {"name": 15683, "value": 50}, {"name": 15718, "value": 50}, {"name": 15723, "value": 50}, {"name": 15740, "value": 50}, {"name": 15743, "value": 50}, {"name": 15749, "value": 50}, {"name": 15760, "value": 50}, {"name": 15763, "value": 50}, {"name": 15887, "value": 50}, {"name": 15926, "value": 50}, {"name": 15958, "value": 50}, {"name": 15961, "value": 50}, {"name": 15976, "value": 50}, {"name": 15979, "value": 50}, {"name": 15992, "value": 50}, {"name": 15993, "value": 50}, {"name": 16005, "value": 50}, {"name": 16044, "value": 50}, {"name": 16050, "value": 50}, {"name": 16058, "value": 50}, {"name": 16065, "value": 50}, {"name": 16072, "value": 50}, {"name": 16088, "value": 50}, {"name": 16090, "value": 50}, {"name": 16103, "value": 50}, {"name": 16155, "value": 50}, {"name": 16163, "value": 50}, {"name": 16165, "value": 50}, {"name": 16198, "value": 50}, {"name": 16470, "value": 50}, {"name": 16641, "value": 50}, {"name": 16776, "value": 50}, {"name": 16815, "value": 50}, {"name": 16862, "value": 50}, {"name": 16896, "value": 50}, {"name": 16898, "value": 50}, {"name": 16900, "value": 50}, {"name": 16909, "value": 50}, {"name": 16949, "value": 50}, {"name": 16951, "value": 50}, {"name": 16970, "value": 50}, {"name": 17218, "value": 50}, {"name": 17359, "value": 50}, {"name": 17382, "value": 50}, {"name": 17403, "value": 50}, {"name": 17410, "value": 50}, {"name": 17414, "value": 50}, {"name": 17423, "value": 50}, {"name": 17490, "value": 50}, {"name": 17492, "value": 50}, {"name": 17587, "value": 50}, {"name": 17596, "value": 50}, {"name": 17634, "value": 50}, {"name": 17736, "value": 50}, {"name": 17739, "value": 50}, {"name": 17797, "value": 50}, {"name": 17833, "value": 50}, {"name": 17914, "value": 50}, {"name": 17942, "value": 50}, {"name": 17946, "value": 50}, {"name": 18062, "value": 50}, {"name": 18212, "value": 50}, {"name": 18275, "value": 50}, {"name": 18354, "value": 50}, {"name": 18411, "value": 50}, {"name": 18414, "value": 50}, {"name": 18425, "value": 50}, {"name": 18438, "value": 50}, {"name": 18439, "value": 50}, {"name": 18480, "value": 50}, {"name": 18510, "value": 50}, {"name": 18511, "value": 50}, {"name": 18512, "value": 50}, {"name": 18516, "value": 50}, {"name": 18550, "value": 50}, {"name": 18561, "value": 50}, {"name": 18578, "value": 50}, {"name": 18599, "value": 50}, {"name": 18657, "value": 50}, {"name": 18664, "value": 50}, {"name": 18667, "value": 50}, {"name": 18713, "value": 50}, {"name": 18786, "value": 50}, {"name": 18791, "value": 50}, {"name": 18848, "value": 50}, {"name": 18897, "value": 50}, {"name": 18898, "value": 50}, {"name": 18951, "value": 50}, {"name": 19016, "value": 50}, {"name": 19033, "value": 50}, {"name": 19053, "value": 50}, {"name": 19078, "value": 50}, {"name": 19080, "value": 50}, {"name": 19082, "value": 50}, {"name": 19096, "value": 50}, {"name": 19131, "value": 50}, {"name": 19137, "value": 50}, {"name": 19148, "value": 50}, {"name": 19163, "value": 50}, {"name": 19164, "value": 50}, {"name": 19172, "value": 50}, {"name": 19214, "value": 50}, {"name": 19239, "value": 50}, {"name": 19246, "value": 50}, {"name": 19252, "value": 50}, {"name": 19253, "value": 50}, {"name": 19270, "value": 50}, {"name": 19273, "value": 50}, {"name": 19275, "value": 50}, {"name": 19334, "value": 50}, {"name": 19372, "value": 50}, {"name": 19383, "value": 50}, {"name": 19420, "value": 50}, {"name": 19428, "value": 50}, {"name": 19449, "value": 50}, {"name": 19459, "value": 50}, {"name": 19460, "value": 50}, {"name": 19520, "value": 50}, {"name": 19555, "value": 50}, {"name": 19599, "value": 50}, {"name": 19620, "value": 50}, {"name": 19644, "value": 50}, {"name": 19648, "value": 50}, {"name": 19701, "value": 50}, {"name": 19785, "value": 50}, {"name": 19905, "value": 50}, {"name": 19907, "value": 50}, {"name": 19908, "value": 50}, {"name": 19912, "value": 50}, {"name": 19946, "value": 50}, {"name": 19952, "value": 50}, {"name": 19955, "value": 50}, {"name": 19956, "value": 50}, {"name": 19957, "value": 50}, {"name": 19960, "value": 50}, {"name": 19963, "value": 50}, {"name": 19966, "value": 50}, {"name": 19976, "value": 50}, {"name": 19998, "value": 50}, {"name": 20105, "value": 50}, {"name": 20182, "value": 50}, {"name": 20188, "value": 50}, {"name": 20282, "value": 50}, {"name": 20431, "value": 50}, {"name": 20435, "value": 50}, {"name": 20436, "value": 50}, {"name": 20453, "value": 50}, {"name": 20470, "value": 50}, {"name": 20493, "value": 50}, {"name": 20614, "value": 50}, {"name": 20625, "value": 50}, {"name": 20639, "value": 50}, {"name": 20683, "value": 50}, {"name": 20687, "value": 50}, {"name": 20689, "value": 50}, {"name": 20734, "value": 50}, {"name": 20740, "value": 50}, {"name": 20753, "value": 50}, {"name": 20756, "value": 50}, {"name": 20778, "value": 50}, {"name": 20781, "value": 50}, {"name": 20793, "value": 50}, {"name": 20794, "value": 50}, {"name": 20813, "value": 50}, {"name": 20913, "value": 50}, {"name": 21000, "value": 50}, {"name": 21003, "value": 50}, {"name": 21023, "value": 50}, {"name": 21028, "value": 50}, {"name": 21030, "value": 50}, {"name": 21031, "value": 50}, {"name": 21074, "value": 50}, {"name": 21087, "value": 50}, {"name": 21119, "value": 50}, {"name": 21133, "value": 50}, {"name": 21152, "value": 50}, {"name": 21378, "value": 50}, {"name": 21675, "value": 50}, {"name": 21700, "value": 50}, {"name": 21761, "value": 50}, {"name": 21791, "value": 50}, {"name": 21802, "value": 50}, {"name": 21806, "value": 50}, {"name": 21863, "value": 50}, {"name": 21865, "value": 50}, {"name": 21885, "value": 50}, {"name": 21905, "value": 50}, {"name": 22129, "value": 50}, {"name": 22199, "value": 50}, {"name": 22288, "value": 50}, {"name": 22379, "value": 50}, {"name": 22382, "value": 50}, {"name": 22396, "value": 50}, {"name": 22442, "value": 50}, {"name": 22444, "value": 50}, {"name": 22446, "value": 50}, {"name": 22447, "value": 50}, {"name": 22511, "value": 50}, {"name": 22530, "value": 50}, {"name": 22596, "value": 50}, {"name": 22604, "value": 50}, {"name": 22611, "value": 50}, {"name": 22619, "value": 50}, {"name": 22675, "value": 50}, {"name": 22696, "value": 50}, {"name": 22709, "value": 50}, {"name": 22710, "value": 50}, {"name": 22715, "value": 50}, {"name": 22720, "value": 50}, {"name": 22723, "value": 50}, {"name": 22731, "value": 50}, {"name": 22764, "value": 50}, {"name": 22764, "value": 50}, {"name": 22797, "value": 50}, {"name": 22802, "value": 50}, {"name": 22814, "value": 50}, {"name": 22853, "value": 50}, {"name": 22869, "value": 50}, {"name": 22870, "value": 50}, {"name": 22881, "value": 50}, {"name": 23005, "value": 50}, {"name": 23017, "value": 50}, {"name": 23033, "value": 50}, {"name": 23036, "value": 50}, {"name": 23074, "value": 50}, {"name": 23077, "value": 50}, {"name": 23108, "value": 50}, {"name": 23133, "value": 50}, {"name": 23704, "value": 50}, {"name": 23840, "value": 50}, {"name": 23841, "value": 50}, {"name": 23956, "value": 50}, {"name": 23978, "value": 50}, {"name": 23979, "value": 50}, {"name": 23984, "value": 50}, {"name": 23993, "value": 50}, {"name": 24191, "value": 50}, {"name": 24245, "value": 50}, {"name": 24247, "value": 50}, {"name": 24303, "value": 50}, {"name": 24633, "value": 50}, {"name": 24639, "value": 50}, {"name": 24680, "value": 50}, {"name": 24725, "value": 50}, {"name": 24899, "value": 50}, {"name": 24908, "value": 50}, {"name": 24940, "value": 50}, {"name": 24971, "value": 50}, {"name": 24994, "value": 50}, {"name": 24998, "value": 50}, {"name": 25027, "value": 50}, {"name": 25060, "value": 50}, {"name": 25069, "value": 50}, {"name": 25081, "value": 50}, {"name": 25191, "value": 50}, {"name": 25206, "value": 50}, {"name": 25224, "value": 50}, {"name": 25232, "value": 50}, {"name": 25324, "value": 50}, {"name": 25390, "value": 50}, {"name": 25393, "value": 50}, {"name": 25724, "value": 50}, {"name": 25737, "value": 50}, {"name": 25764, "value": 50}, {"name": 25776, "value": 50}, {"name": 25784, "value": 50}, {"name": 25798, "value": 50}, {"name": 25850, "value": 50}, {"name": 25854, "value": 50}, {"name": 25860, "value": 50}, {"name": 25925, "value": 50}, {"name": 25953, "value": 50}, {"name": 25982, "value": 50}, {"name": 25988, "value": 50}, {"name": 26056, "value": 50}, {"name": 26143, "value": 50}, {"name": 26147, "value": 50}, {"name": 26153, "value": 50}, {"name": 26250, "value": 50}, {"name": 26449, "value": 50}, {"name": 26496, "value": 50}, {"name": 26518, "value": 50}, {"name": 26564, "value": 50}, {"name": 26707, "value": 50}, {"name": 26758, "value": 50}, {"name": 26862, "value": 50}, {"name": 26863, "value": 50}, {"name": 26934, "value": 50}, {"name": 26946, "value": 50}, {"name": 26956, "value": 50}, {"name": 27020, "value": 50}, {"name": 27148, "value": 50}, {"name": 27195, "value": 50}, {"name": 27214, "value": 50}, {"name": 27245, "value": 50}, {"name": 27283, "value": 50}, {"name": 27310, "value": 50}, {"name": 27362, "value": 50}, {"name": 27667, "value": 50}, {"name": 27727, "value": 50}, {"name": 27728, "value": 50}, {"name": 27739, "value": 50}, {"name": 27757, "value": 50}, {"name": 27761, "value": 50}, {"name": 27780, "value": 50}, {"name": 27798, "value": 50}, {"name": 27884, "value": 50}, {"name": 27899, "value": 50}, {"name": 28118, "value": 50}, {"name": 28154, "value": 50}, {"name": 28179, "value": 50}, {"name": 28181, "value": 50}, {"name": 28204, "value": 50}, {"name": 28221, "value": 50}, {"name": 28225, "value": 50}, {"name": 28255, "value": 50}, {"name": 28314, "value": 50}, {"name": 28321, "value": 50}, {"name": 28507, "value": 50}, {"name": 28511, "value": 50}, {"name": 28529, "value": 50}, {"name": 28537, "value": 50}, {"name": 28539, "value": 50}, {"name": 28541, "value": 50}, {"name": 28592, "value": 50}, {"name": 28597, "value": 50}, {"name": 28600, "value": 50}, {"name": 28639, "value": 50}, {"name": 28659, "value": 50}, {"name": 28670, "value": 50}, {"name": 28676, "value": 50}, {"name": 28677, "value": 50}, {"name": 28684, "value": 50}, {"name": 28687, "value": 50}, {"name": 28691, "value": 50}, {"name": 28710, "value": 50}, {"name": 28720, "value": 50}, {"name": 28734, "value": 50}, {"name": 28794, "value": 50}, {"name": 28834, "value": 50}, {"name": 28864, "value": 50}, {"name": 29000, "value": 50}, {"name": 29004, "value": 50}, {"name": 29006, "value": 50}, {"name": 29049, "value": 50}, {"name": 29062, "value": 50}, {"name": 29078, "value": 50}, {"name": 29112, "value": 50}, {"name": 29128, "value": 50}, {"name": 29138, "value": 50}, {"name": 29242, "value": 50}, {"name": 29287, "value": 50}, {"name": 29295, "value": 50}, {"name": 29338, "value": 50}, {"name": 29383, "value": 50}, {"name": 30249, "value": 50}, {"name": 30253, "value": 50}, {"name": 30256, "value": 50}, {"name": 30260, "value": 50}, {"name": 30261, "value": 50}, {"name": 30263, "value": 50}, {"name": 30275, "value": 50}, {"name": 30303, "value": 50}, {"name": 30350, "value": 50}, {"name": 30352, "value": 50}, {"name": 30383, "value": 50}, {"name": 30432, "value": 50}, {"name": 30437, "value": 50}, {"name": 30456, "value": 50}, {"name": 30512, "value": 50}, {"name": 30522, "value": 50}, {"name": 30537, "value": 50}, {"name": 30561, "value": 50}, {"name": 30582, "value": 50}, {"name": 30595, "value": 50}, {"name": 30599, "value": 50}, {"name": 30680, "value": 50}, {"name": 30779, "value": 50}, {"name": 30797, "value": 50}, {"name": 31113, "value": 50}, {"name": 31116, "value": 50}, {"name": 31121, "value": 50}, {"name": 31128, "value": 50}, {"name": 31134, "value": 50}, {"name": 31142, "value": 50}, {"name": 31160, "value": 50}, {"name": 31165, "value": 50}, {"name": 31169, "value": 50}, {"name": 31174, "value": 50}, {"name": 31181, "value": 50}, {"name": 31183, "value": 50}, {"name": 31208, "value": 50}, {"name": 31209, "value": 50}, {"name": 31224, "value": 50}, {"name": 31246, "value": 50}, {"name": 31250, "value": 50}, {"name": 31253, "value": 50}, {"name": 31255, "value": 50}, {"name": 31293, "value": 50}, {"name": 31304, "value": 50}, {"name": 31313, "value": 50}, {"name": 31318, "value": 50}, {"name": 31330, "value": 50}, {"name": 31332, "value": 50}, {"name": 31386, "value": 50}, {"name": 31389, "value": 50}, {"name": 31390, "value": 50}, {"name": 31393, "value": 50}, {"name": 31398, "value": 50}, {"name": 31423, "value": 50}, {"name": 31492, "value": 50}, {"name": 31515, "value": 50}, {"name": 31519, "value": 50}, {"name": 31536, "value": 50}, {"name": 31559, "value": 50}, {"name": 31690, "value": 50}, {"name": 31775, "value": 50}, {"name": 31904, "value": 50}, {"name": 32122, "value": 50}, {"name": 32155, "value": 50}, {"name": 32186, "value": 50}, {"name": 32259, "value": 50}, {"name": 32262, "value": 50}, {"name": 32316, "value": 50}, {"name": 32324, "value": 50}, {"name": 32334, "value": 50}, {"name": 32383, "value": 50}, {"name": 32421, "value": 50}, {"name": 32462, "value": 50}, {"name": 32471, "value": 50}, {"name": 32488, "value": 50}, {"name": 32512, "value": 50}, {"name": 32545, "value": 50}, {"name": 32555, "value": 50}, {"name": 32567, "value": 50}, {"name": 32572, "value": 50}, {"name": 32574, "value": 50}, {"name": 32580, "value": 50}, {"name": 32585, "value": 50}, {"name": 32592, "value": 50}, {"name": 32593, "value": 50}, {"name": 32595, "value": 50}, {"name": 32604, "value": 50}, {"name": 32613, "value": 50}, {"name": 32616, "value": 50}, {"name": 32643, "value": 50}, {"name": 32660, "value": 50}, {"name": 32710, "value": 50}, {"name": 32788, "value": 50}, {"name": 32826, "value": 50}, {"name": 32827, "value": 50}, {"name": 32849, "value": 50}, {"name": 32853, "value": 50}, {"name": 32933, "value": 50}, {"name": 33004, "value": 50}, {"name": 33030, "value": 50}, {"name": 33036, "value": 50}, {"name": 33037, "value": 50}, {"name": 33045, "value": 50}, {"name": 33056, "value": 50}, {"name": 33062, "value": 50}, {"name": 33065, "value": 50}, {"name": 33067, "value": 50}, {"name": 33068, "value": 50}, {"name": 33076, "value": 50}, {"name": 33080, "value": 50}, {"name": 33081, "value": 50}, {"name": 33086, "value": 50}, {"name": 33109, "value": 50}, {"name": 33129, "value": 50}, {"name": 33139, "value": 50}, {"name": 33170, "value": 50}, {"name": 33184, "value": 50}, {"name": 33193, "value": 50}, {"name": 33262, "value": 50}, {"name": 33297, "value": 50}, {"name": 33316, "value": 50}, {"name": 33415, "value": 50}, {"name": 33418, "value": 50}, {"name": 33435, "value": 50}, {"name": 33492, "value": 50}, {"name": 33495, "value": 50}, {"name": 33500, "value": 50}, {"name": 33502, "value": 50}, {"name": 33609, "value": 50}, {"name": 33640, "value": 50}, {"name": 33642, "value": 50}, {"name": 33643, "value": 50}, {"name": 33644, "value": 50}, {"name": 33646, "value": 50}, {"name": 33655, "value": 50}, {"name": 33673, "value": 50}, {"name": 33699, "value": 50}, {"name": 33702, "value": 50}, {"name": 33705, "value": 50}, {"name": 33712, "value": 50}, {"name": 33713, "value": 50}, {"name": 33715, "value": 50}, {"name": 33740, "value": 50}, {"name": 33759, "value": 50}, {"name": 33798, "value": 50}, {"name": 33882, "value": 50}, {"name": 33897, "value": 50}, {"name": 34084, "value": 50}, {"name": 34087, "value": 50}, {"name": 34089, "value": 50}, {"name": 34100, "value": 50}, {"name": 34113, "value": 50}, {"name": 34156, "value": 50}, {"name": 34164, "value": 50}, {"name": 34166, "value": 50}, {"name": 34176, "value": 50}, {"name": 34180, "value": 50}, {"name": 34203, "value": 50}, {"name": 34231, "value": 50}, {"name": 34234, "value": 50}, {"name": 34246, "value": 50}, {"name": 34261, "value": 50}, {"name": 34271, "value": 50}, {"name": 34275, "value": 50}, {"name": 34287, "value": 50}, {"name": 34291, "value": 50}, {"name": 34297, "value": 50}, {"name": 34311, "value": 50}, {"name": 34313, "value": 50}, {"name": 34318, "value": 50}, {"name": 34334, "value": 50}, {"name": 34355, "value": 50}, {"name": 34359, "value": 50}, {"name": 34514, "value": 50}, {"name": 34614, "value": 50}, {"name": 34631, "value": 50}, {"name": 34652, "value": 50}, {"name": 34655, "value": 50}, {"name": 34658, "value": 50}, {"name": 34661, "value": 50}, {"name": 34680, "value": 50}, {"name": 34681, "value": 50}, {"name": 34682, "value": 50}, {"name": 34691, "value": 50}, {"name": 34710, "value": 50}, {"name": 34723, "value": 50}, {"name": 34726, "value": 50}, {"name": 34728, "value": 50}, {"name": 34732, "value": 50}, {"name": 34734, "value": 50}, {"name": 34739, "value": 50}, {"name": 34742, "value": 50}, {"name": 34747, "value": 50}, {"name": 34754, "value": 50}, {"name": 34756, "value": 50}, {"name": 34759, "value": 50}, {"name": 34762, "value": 50}, {"name": 34765, "value": 50}, {"name": 34770, "value": 50}, {"name": 34779, "value": 50}, {"name": 34780, "value": 50}, {"name": 34788, "value": 50}, {"name": 34790, "value": 50}, {"name": 34804, "value": 50}, {"name": 34838, "value": 50}, {"name": 34860, "value": 50}, {"name": 34874, "value": 50}, {"name": 34881, "value": 50}, {"name": 35001, "value": 50}, {"name": 35031, "value": 50}, {"name": 35032, "value": 50}, {"name": 35045, "value": 50}, {"name": 35052, "value": 50}, {"name": 35056, "value": 50}, {"name": 35064, "value": 50}, {"name": 35065, "value": 50}, {"name": 35066, "value": 50}, {"name": 35070, "value": 50}, {"name": 35071, "value": 50}, {"name": 35073, "value": 50}, {"name": 35076, "value": 50}, {"name": 35079, "value": 50}, {"name": 35081, "value": 50}, {"name": 35092, "value": 50}, {"name": 35093, "value": 50}, {"name": 35103, "value": 50}, {"name": 35105, "value": 50}, {"name": 35109, "value": 50}, {"name": 35123, "value": 50}, {"name": 35140, "value": 50}, {"name": 35146, "value": 50}, {"name": 35151, "value": 50}, {"name": 35207, "value": 50}, {"name": 35221, "value": 50}, {"name": 35228, "value": 50}, {"name": 35259, "value": 50}, {"name": 35269, "value": 50}, {"name": 35279, "value": 50}, {"name": 35283, "value": 50}, {"name": 35289, "value": 50}, {"name": 35296, "value": 50}, {"name": 35415, "value": 50}, {"name": 35465, "value": 50}, {"name": 35498, "value": 50}, {"name": 35500, "value": 50}, {"name": 35553, "value": 50}, {"name": 35557, "value": 50}, {"name": 35561, "value": 50}, {"name": 35592, "value": 50}, {"name": 35596, "value": 50}, {"name": 35620, "value": 50}, {"name": 35628, "value": 50}, {"name": 35640, "value": 50}, {"name": 35673, "value": 50}, {"name": 35726, "value": 50}, {"name": 50017, "value": 50}, {"name": 50117, "value": 50}, {"name": 50147, "value": 50}, {"name": 50164, "value": 50}, {"name": 50172, "value": 50}, {"name": 50268, "value": 50}, {"name": 50375, "value": 50}, {"name": 50456, "value": 50}]
    # {"24": [-122.2715, 37.5095], "28": [-115.0215, 35.9515], "32": [-117.1815, 32.8885], "75": [-77.7395, 38.9695], "85": [-87.6285, 41.8795], "97": [-111.8785, 40.7805], "125": [-117.1615, 32.7195], "131": [-122.2815, 37.8275], "146": [-121.9305, 37.4905], "190": [-71.0585, 42.3575], "202": [-105.0925, 39.7985], "319": [-117.2425, 32.8815], "331": [-117.2315, 32.8775], "345": [-121.8105, 37.3095], "394": [-79.1485, 37.4195], "468": [-81.5695, 41.4715], "591": [-122.1585, 37.4575], "801": [-93.3225, 44.9175], "1053": [-122.4405, 37.7485], "1058": [-122.5705, 47.6615], "1101": [-122.0825, 37.4175], "1105": [-83.7425, 42.2795], "1107": [-90.1825, 32.3005], "1113": [-77.0525, 38.7985], "1119": [-122.0425, 47.3615], "1121": [-96.6415, 32.9075], "1123": [-74.4315, 39.4885], "1127": [-76.8515, 39.1005], "1131": [-83.8515, 42.2675], "1132": [-122.1415, 37.4385], "1133": [-80.3615, 25.6685], "1134": [-73.9515, 40.8095], "1136": [-122.1215, 47.6705], "1145": [-122.1305, 48.0495], "1149": [-81.1205, 28.7415], "1160": [-77.5195, 38.9875], "1163": [-89.3895, 43.0685], "1169": [-76.9395, 38.9915], "1171": [-122.2095, 37.4875], "1179": [-71.2295, 42.2315], "1184": [-87.1685, 39.0295], "1185": [-71.1185, 42.3795], "1186": [-122.4185, 37.7505], "1188": [-121.8885, 37.3015], "1189": [-73.7785, 40.9115], "1194": [-105.0285, 39.5795], "1196": [-122.0885, 37.6905], "1198": [-96.6785, 33.0315], "1408": [-77.3625, 38.9515], "2285": [-122.5685, 47.6095], "2289": [-121.8885, 37.3115], "2427": [-77.0215, 34.6705], "2529": [-71.4215, 42.2815], "2549": [-87.8005, 42.1815], "2591": [-118.3885, 33.9275], "2592": [-122.3285, 47.6085], "2627": [-111.7215, 40.3405], "2685": [-80.3285, 25.7795], "2711": [-81.4925, 41.0275], "2858": [-87.9705, 42.0015], "3041": [-87.9105, 43.0375], "3103": [-77.7025, 39.6585], "3218": [-71.0825, 42.3615], "3252": [-71.0805, 42.3585], "3280": [-74.0085, 40.7075], "3410": [-77.5025, 38.9675], "3423": [-84.0815, 40.7985], "3483": [-123.0885, 44.0485], "3517": [-88.0225, 44.5205], "3524": [-123.0515, 44.0395], "3525": [-82.8815, 40.0195], "3574": [-76.9495, 39.3995], "3579": [-95.3695, 29.7615], "3588": [-147.1185, 64.8615], "3600": [-71.1025, 42.3875], "3620": [-75.1515, 40.1575], "3640": [-76.8605, 39.1975], "3644": [-84.2205, 33.8495], "3645": [-121.7505, 38.5695], "3649": [-77.0505, 38.9215], "3650": [-122.3305, 47.6075], "3651": [-122.2905, 37.8675], "3656": [-122.6805, 45.5205], "3658": [-76.9705, 39.3715], "3660": [-84.2995, 33.8875], "3663": [-122.1195, 37.4285], "3666": [-77.8595, 40.7905], "3669": [-122.0295, 37.3515], "3670": [-121.6995, 38.5575], "3671": [-122.6095, 45.5075], "3673": [-122.0595, 37.3885], "3683": [-77.0885, 38.8785], "3685": [-122.0785, 37.3895], "3686": [-71.4685, 42.4805], "3715": [-77.1625, 38.9795], "3724": [-74.0115, 40.7795], "3737": [-77.3715, 39.0405], "3753": [-104.9905, 39.7385], "3756": [-75.5205, 40.1105], "3767": [-71.5695, 42.6105], "3964": [-71.4495, 42.9995], "4019": [-87.6525, 41.8915], "4069": [-79.3295, 40.8215], "4085": [-87.9885, 42.2695], "4111": [-121.8725, 37.2075], "4148": [-77.9005, 40.7915], "4155": [-119.8105, 39.5295], "4279": [-71.2195, 42.7915], "4304": [-121.9325, 37.3095], "4307": [-122.2925, 37.5405], "4334": [-96.9215, 46.8295], "4405": [-72.6625, 44.1095], "4412": [-73.9525, 40.6485], "4417": [-80.5925, 28.0305], "4549": [-71.4405, 42.3315], "4551": [-71.5705, 42.6675], "4602": [-117.0025, 46.7285], "4674": [-75.7695, 39.7795], "4706": [-121.3425, 38.5905], "4894": [-84.3185, 33.8495], "4930": [-122.0715, 37.3675], "4958": [-77.4605, 39.0215], "4959": [-96.8205, 32.8015], "4969": [-78.9395, 35.9915], "4981": [-122.3385, 47.6075], "6045": [-122.1405, 37.4395], "6061": [-96.8195, 32.7975], "6062": [-80.2295, 25.7885], "6065": [-122.3395, 47.6095], "6066": [-84.4195, 33.7705], "6067": [-96.8595, 32.8105], "6072": [-75.6095, 39.9585], "6074": [-122.3995, 37.7195], "6080": [-104.9785, 39.7375], "6092": [-77.4885, 39.0385], "6093": [-96.9285, 32.9885], "6095": [-122.3985, 37.7195], "6097": [-84.6685, 42.7105], "6101": [-112.0125, 33.4175], "6125": [-118.4015, 33.9195], "6130": [-77.3715, 38.9475], "6140": [-77.4605, 39.0175], "6144": [-77.4905, 39.0395], "6147": [-80.1905, 25.7805], "6155": [-77.0205, 38.8995], "6156": [-122.4205, 37.7705], "6201": [-119.8225, 39.5375], "6208": [-113.6225, 37.0815], "6216": [-95.2625, 38.9505], "6222": [-71.0615, 42.3485], "6223": [-74.6515, 40.3485], "6229": [-117.2415, 32.8815], "6231": [-71.1115, 42.3475], "6236": [-81.8715, 35.3305], "6247": [-80.4105, 37.2005], "6257": [-94.7505, 38.9305], "6259": [-87.6305, 41.8815], "6264": [-122.3295, 47.6095], "6265": [-96.7995, 32.7795], "6266": [-80.1895, 25.7605], "6274": [-122.2895, 47.4995], "6280": [-87.9685, 41.9975], "6285": [-84.3885, 33.7495], "6286": [-74.0085, 40.7105], "6287": [-96.5185, 48.5805], "6288": [-75.1685, 39.9515], "6289": [-77.4885, 39.0415], "6290": [-121.8885, 37.3375], "6292": [-104.9885, 39.7385], "6341": [-77.4305, 38.8875], "6343": [-87.6205, 41.8485], "6355": [-77.4905, 39.0395], "6373": [-94.5795, 39.0985], "6379": [-78.8795, 35.9315], "6388": [-80.0385, 40.4315], "6389": [-83.2585, 42.4515], "6394": [-122.6785, 45.5195], "6407": [-122.3625, 47.6205], "6408": [-112.0125, 33.4215], "6409": [-96.8825, 32.8415], "6411": [-121.7825, 37.2375], "10007": [-122.3325, 38.3305], "10009": [-122.2725, 37.5115], "10099": [-84.4085, 33.9615], "10185": [-117.1985, 32.8595], "10194": [-87.9985, 41.8795], "10204": [-71.1525, 42.3795], "10284": [-122.4785, 37.7895], "10286": [-87.1685, 39.0305], "10301": [-93.2725, 44.9775], "10303": [-122.6825, 45.5185], "10305": [-121.9425, 37.2795], "10312": [-79.7925, 36.0685], "10317": [-97.1525, 32.6705], "10322": [-71.0615, 42.0385], "10329": [-77.3415, 38.9615], "10331": [-122.1215, 47.4775], "10333": [-75.1715, 39.9485], "10334": [-105.1715, 40.0995], "10335": [-71.1015, 42.3695], "10338": [-83.4615, 42.3215], "10342": [-117.0005, 46.7285], "10343": [-117.4005, 33.9485], "10350": [-77.3805, 37.6775], "10355": [-75.4205, 39.8795], "10356": [-74.6105, 39.2505], "10357": [-75.5205, 39.1605], "10360": [-82.7595, 27.8575], "10362": [-83.7395, 42.2485], "10369": [-91.1195, 30.4515], "10371": [-74.0095, 40.8875], "10377": [-75.8495, 42.9305], "10381": [-122.3285, 37.5575], "10386": [-74.4285, 39.4905], "10390": [-84.5685, 42.8375], "10394": [-112.2885, 33.7095], "10399": [-75.6085, 40.0915], "10400": [-81.6425, 28.7975], "10402": [-71.5225, 42.3085], "10403": [-122.0725, 36.9985], "10406": [-86.9825, 40.2005], "10413": [-89.5325, 43.0685], "10415": [-122.4025, 37.7195], "10418": [-89.4325, 43.0115], "10423": [-77.6515, 37.5085], "10427": [-73.6315, 40.7305], "10443": [-73.2005, 44.4685], "10445": [-78.6705, 38.6495], "10456": [-112.0705, 33.4505], "10457": [-122.4005, 37.7805], "10458": [-75.6505, 41.4915], "10462": [-77.5295, 38.9785], "10465": [-97.1095, 32.7395], "10473": [-73.1295, 44.5285], "10478": [-87.8995, 41.8915], "10482": [-75.3385, 39.8585], "10484": [-76.9885, 38.8895], "10486": [-122.6385, 48.2905], "10491": [-75.1585, 39.9475], "10495": [-90.0785, 29.9495], "10498": [-78.8785, 42.8915], "10506": [-97.8225, 37.7505], "10507": [-97.8225, 37.7505], "10515": [-80.1425, 26.6095], "10518": [-93.3625, 45.0315], "10540": [-88.1105, 42.0075], "10542": [-87.7905, 41.7385], "10543": [-81.7305, 28.7985], "10544": [-87.6905, 42.0695], "10545": [-88.1405, 41.3195], "10551": [-77.2305, 39.9775], "10553": [-73.4305, 41.3585], "10555": [-85.6205, 42.2995], "10556": [-88.0905, 41.8405], "10562": [-71.1395, 42.2785], "10564": [-95.9895, 36.1495], "10565": [-95.5995, 29.6695], "10568": [-75.1695, 40.2015], "10576": [-77.5995, 38.8105], "10584": [-75.9185, 40.3495], "10587": [-111.9085, 33.3805], "10595": [-95.6985, 29.9695], "10597": [-71.1085, 42.3705], "10598": [-78.0185, 40.7915], "10599": [-74.2285, 39.5815], "10626": [-104.8315, 39.0505], "10637": [-111.9115, 40.8405], "10640": [-122.2905, 47.4875], "10657": [-95.4305, 29.9405], "10668": [-122.2095, 37.5015], "10674": [-121.9595, 37.3795], "10675": [-77.4695, 38.9095], "10677": [-96.8295, 32.9305], "10692": [-77.4885, 39.0385], "10693": [-72.9685, 43.5685], "10694": [-77.3885, 38.9695], "10704": [-80.7925, 28.1995], "10727": [-77.0715, 38.9005], "10743": [-122.3105, 47.6185], "10751": [-77.0005, 39.1075], "10790": [-104.9785, 39.7375], "10814": [-83.7425, 42.2795], "10884": [-71.4585, 42.2895], "10905": [-110.9325, 32.2195], "11010": [-75.3925, 39.9175], "11018": [-68.6725, 44.8815], "11090": [-117.1585, 32.7375], "11171": [-74.1395, 40.3975], "11203": [-74.1425, 40.3685], "11207": [-87.9825, 42.0905], "11215": [-77.4625, 39.0195], "11500": [-75.1825, 39.4175], "11513": [-83.5925, 42.2585], "11528": [-121.8915, 37.3415], "11529": [-84.0915, 39.7415], "11536": [-122.0815, 37.3905], "11550": [-77.3105, 38.9675], "11582": [-118.2385, 34.0485], "11634": [-113.6215, 37.1195], "11689": [-95.3885, 45.6515], "11705": [-122.3025, 47.7595], "11747": [-75.6605, 41.4105], "11765": [-80.1895, 40.5495], "11795": [-78.8785, 35.8595], "11797": [-78.8485, 35.7305], "11801": [-71.0825, 42.3575], "11857": [-87.9405, 42.0705], "11911": [-79.9625, 40.3675], "11985": [-75.5385, 40.1795], "11989": [-122.0985, 37.4015], "12012": [-74.5725, 39.9885], "12016": [-71.0425, 42.3705], "12030": [-122.3215, 47.8175], "12060": [-88.2795, 42.0375], "12070": [-84.5395, 33.8275], "12100": [-112.0725, 33.4475], "12103": [-121.0525, 40.2985], "12105": [-110.7525, 32.0795], "12108": [-96.8225, 32.9815], "12115": [-74.2625, 40.6995], "12116": [-118.4625, 34.0005], "12121": [-120.1815, 39.3275], "12134": [-117.8315, 33.6795], "12144": [-84.3905, 33.7495], "12146": [-82.0405, 34.7405], "12154": [-117.1405, 32.7695], "12156": [-89.5305, 40.9005], "12159": [-108.7605, 44.7515], "12161": [-81.8595, 41.1375], "12166": [-86.2695, 41.8205], "12180": [-86.9385, 36.0575], "12215": [-122.2625, 37.7695], "12226": [-122.0315, 36.9705], "12297": [-74.6685, 40.3605], "12300": [-121.8925, 37.3275], "12303": [-95.7125, 37.0885], "12315": [-73.4125, 41.0895], "12316": [-75.4225, 40.5305], "12318": [-90.4725, 38.5415], "12320": [-82.3615, 29.6775], "12330": [-90.4915, 38.7775], "12331": [-77.3915, 39.4475], "12380": [-82.1485, 34.9375], "12402": [-81.6025, 39.2785], "12426": [-120.9015, 40.1205], "12443": [-75.5405, 40.5985], "12452": [-87.7905, 41.8485], "12459": [-77.6305, 39.1915], "12475": [-79.9995, 39.9995], "12504": [-104.8425, 39.6595], "12506": [-77.4625, 39.0205], "12518": [-74.6425, 40.1315], "12548": [-86.6305, 39.2315], "12563": [-74.7495, 41.0585], "12578": [-93.2295, 44.9715], "12579": [-121.8895, 37.3415], "12588": [-105.2085, 40.0015], "12600": [-122.0225, 37.3675], "12611": [-122.3325, 47.6175], "12621": [-123.2215, 39.2575], "12622": [-122.3115, 47.6785], "12623": [-97.7615, 30.3985], "12650": [-71.5505, 42.8775], "12652": [-122.1905, 47.7185], "12668": [-76.6495, 39.0615], "12671": [-121.8895, 37.3375], "12673": [-75.4495, 38.3985], "12681": [-122.3885, 47.6775], "12685": [-80.1485, 26.0095], "12686": [-73.7085, 41.6205], "12688": [-87.7285, 41.9615], "12691": [-121.8485, 37.3475], "12692": [-82.4585, 40.0685], "12693": [-73.2885, 41.4885], "12695": [-75.3985, 39.9495], "12710": [-121.9725, 36.9475], "12726": [-81.5615, 38.3705], "12728": [-122.1115, 37.3915], "12739": [-76.6715, 42.5415], "12768": [-96.5495, 32.9215], "12788": [-122.4885, 37.7815], "12842": [-83.0405, 34.7585], "12853": [-105.0905, 39.6485], "12863": [-122.7395, 45.8985], "12879": [-72.5895, 42.8415], "12908": [-121.8325, 37.2315], "12920": [-83.8915, 42.2575], "12925": [-122.2715, 37.8795], "12938": [-122.9015, 48.4915], "12984": [-122.4185, 37.7695], "12999": [-121.5985, 37.0315], "13004": [-121.8925, 37.3295], "13056": [-122.4205, 37.7705], "13070": [-122.4195, 37.7675], "13109": [-71.1125, 42.3715], "13120": [-71.1115, 42.3675], "13128": [-77.0715, 39.0015], "13131": [-75.4015, 40.2175], "13146": [-74.0105, 40.7105], "13159": [-70.8705, 43.1715], "13191": [-122.1085, 37.3875], "13205": [-121.9025, 37.7595], "13222": [-121.9315, 37.2785], "13249": [-77.3305, 38.9415], "13253": [-121.8605, 37.2785], "13266": [-86.5595, 34.7405], "13283": [-96.7085, 32.9885], "13288": [-71.7385, 43.6415], "13311": [-77.3825, 38.9575], "13318": [-76.3925, 39.3315], "13334": [-72.6915, 41.7695], "13396": [-74.4285, 40.5405], "13397": [-91.0885, 30.3605], "13499": [-84.3185, 39.2815], "13514": [-87.6525, 41.8495], "13520": [-122.3315, 47.6075], "13528": [-96.8215, 32.7815], "13547": [-83.6705, 42.2205], "13551": [-89.6005, 40.7675], "13561": [-121.8995, 37.3275], "13565": [-118.2395, 34.0495], "13572": [-77.2495, 38.6585], "13585": [-122.3885, 37.7695], "13614": [-122.2525, 37.8795], "13639": [-84.0915, 34.2615], "13651": [-86.3905, 35.8475], "13654": [-73.3905, 41.3895], "13666": [-95.6195, 30.0405], "13671": [-123.1095, 44.0575], "13673": [-86.1595, 39.7685], "13676": [-75.2195, 38.4605], "13681": [-77.4185, 38.9575], "13688": [-74.9885, 40.0515], "13694": [-96.7885, 33.0395], "13735": [-77.8715, 40.8095], "13826": [-122.0715, 37.0505], "13831": [-117.1915, 34.4975], "13834": [-84.0815, 33.8695], "13838": [-73.9915, 40.8615], "13864": [-71.1195, 42.3795], "13942": [-84.6505, 42.6485], "13960": [-122.6395, 38.2275], "14053": [-82.7305, 27.9285], "14064": [-84.1795, 39.5595], "14066": [-122.8095, 45.4905], "14069": [-96.8795, 32.8215], "14071": [-82.9095, 40.4175], "14090": [-93.1785, 44.7075], "14102": [-84.0525, 35.0685], "14114": [-96.8225, 32.7995], "14132": [-81.0415, 35.2385], "14164": [-117.1495, 47.6595], "14166": [-117.1695, 47.6505], "14226": [-121.6315, 37.1205], "14227": [-121.8515, 37.2205], "14233": [-105.0215, 39.5385], "14237": [-77.6415, 38.8105], "14242": [-122.2305, 47.7585], "14244": [-93.8505, 38.5895], "14300": [-131.6525, 55.3375], "14324": [-93.1615, 45.1495], "14337": [-71.0215, 42.6005], "14340": [-122.1705, 37.8575], "14546": [-85.9105, 42.4205], "14578": [-122.0895, 37.4215], "14583": [-121.8485, 37.2185], "14604": [-78.5625, 38.8195], "14606": [-156.0225, 20.7805], "14720": [-157.8215, 21.2975], "14748": [-73.1705, 41.3215], "14750": [-81.8805, 26.6375], "14777": [-71.0895, 42.4005], "14795": [-74.0185, 40.7595], "14796": [-87.9385, 41.9005], "14881": [-123.0885, 44.0475], "14882": [-73.1185, 40.9085], "14981": [-73.1285, 40.7875], "15015": [-77.4625, 39.0195], "15035": [-78.5015, 35.9695], "15038": [-92.8615, 45.0715], "15039": [-77.5315, 38.9915], "15086": [-85.9885, 42.8905], "15133": [-122.7915, 45.4485], "15145": [-122.6405, 45.5695], "15387": [-73.9885, 40.7205], "15542": [-97.6505, 30.3785], "15605": [-122.0225, 37.3195], "15619": [-75.4425, 40.0715], "15683": [-97.7985, 30.1685], "15718": [-76.1425, 43.0515], "15723": [-97.1115, 44.8985], "15740": [-75.9005, 42.5375], "15743": [-88.2305, 43.0085], "15749": [-117.8905, 34.1015], "15760": [-68.6695, 44.8675], "15763": [-71.0895, 42.3385], "15887": [-118.4485, 34.0705], "15926": [-119.8915, 39.5505], "15958": [-118.5405, 34.4615], "15961": [-84.1895, 40.5675], "15976": [-77.3495, 38.9305], "15979": [-116.2195, 43.6515], "15992": [-80.1885, 25.7685], "15993": [-122.2685, 37.8685], "16005": [-82.3025, 28.5195], "16044": [-88.2305, 40.1095], "16050": [-72.8405, 41.9175], "16058": [-119.1805, 34.2315], "16065": [-155.9995, 20.7695], "16072": [-122.5795, 45.6885], "16088": [-84.8585, 39.7415], "16090": [-156.4985, 20.8775], "16103": [-74.4825, 40.7785], "16155": [-122.4305, 37.7895], "16163": [-87.6495, 40.1185], "16165": [-74.0295, 40.9895], "16198": [-122.2985, 47.6315], "16470": [-105.1395, 39.9875], "16641": [-121.8205, 37.3675], "16776": [-73.1495, 40.8505], "16815": [-122.2725, 37.7995], "16862": [-122.4295, 37.7485], "16896": [-92.5585, 45.4005], "16898": [-77.9685, 40.2215], "16900": [-77.1525, 38.8375], "16909": [-87.9825, 42.0915], "16949": [-117.8305, 33.8715], "16951": [-118.0205, 33.7075], "16970": [-122.0795, 37.3875], "17218": [-112.0225, 40.4915], "17359": [-77.3805, 38.9815], "17382": [-104.6885, 38.9285], "17403": [-71.1425, 42.6585], "17410": [-77.1525, 38.8375], "17414": [-122.2325, 37.8395], "17423": [-77.3515, 38.9285], "17490": [-71.6285, 42.8575], "17492": [-80.3985, 37.2185], "17587": [-121.9685, 47.6305], "17596": [-83.7385, 42.2505], "17634": [-86.4915, 39.1695], "17736": [-74.0115, 40.7205], "17739": [-95.3715, 29.7615], "17797": [-122.3885, 37.7805], "17833": [-118.2615, 34.0485], "17914": [-97.3025, 32.9495], "17942": [-94.5705, 39.0185], "17946": [-77.8805, 40.3805], "18062": [-122.6895, 45.5585], "18212": [-72.5325, 40.9885], "18275": [-122.4195, 37.7695], "18354": [-98.4905, 29.4295], "18411": [-105.1025, 40.5775], "18414": [-105.1225, 40.1395], "18425": [-87.6315, 41.9095], "18438": [-96.7615, 32.8615], "18439": [-123.9415, 45.6115], "18480": [-70.9385, 43.0775], "18510": [-71.5525, 42.2175], "18511": [-111.8425, 40.5575], "18512": [-118.2425, 34.0485], "18516": [-122.2425, 37.8405], "18550": [-82.6405, 27.7675], "18561": [-97.9295, 30.6875], "18578": [-81.5995, 39.2815], "18599": [-122.2685, 37.8715], "18657": [-159.3505, 22.0805], "18664": [-105.2595, 40.0095], "18667": [-71.4895, 42.8705], "18713": [-70.3025, 41.6985], "18786": [-71.7985, 43.8605], "18791": [-122.2085, 47.7575], "18848": [-90.2505, 38.6415], "18897": [-77.6785, 43.0805], "18898": [-76.1885, 39.5115], "18951": [-73.9405, 40.6875], "19016": [-104.9925, 39.7405], "19033": [-84.1915, 40.0285], "19053": [-155.6705, 20.0085], "19078": [-88.7295, 41.8715], "19080": [-118.3385, 33.8375], "19082": [-96.8285, 33.0085], "19096": [-118.2585, 34.0505], "19131": [-122.9415, 45.5175], "19137": [-86.5215, 39.1705], "19148": [-122.4605, 37.7615], "19163": [-122.5895, 45.4885], "19164": [-121.8795, 37.6495], "19172": [-121.8695, 37.3885], "19214": [-71.0725, 42.3395], "19239": [-122.2715, 37.8815], "19246": [-122.4305, 37.7705], "19252": [-88.9505, 39.8685], "19253": [-122.4305, 37.7585], "19270": [-112.3495, 33.4375], "19273": [-117.6095, 34.0685], "19275": [-71.2095, 42.3495], "19334": [-111.8915, 33.4295], "19372": [-122.0195, 37.4085], "19383": [-121.9985, 37.3185], "19420": [-78.8315, 35.8175], "19428": [-76.6315, 39.2815], "19449": [-78.7105, 35.7415], "19459": [-96.3805, 32.9415], "19460": [-122.3395, 47.6075], "19520": [-122.3415, 47.6175], "19555": [-78.6405, 35.6995], "19599": [-121.4285, 37.7415], "19620": [-112.0415, 40.6275], "19644": [-72.2505, 43.6395], "19648": [-116.9005, 47.8115], "19701": [-121.9225, 37.4675], "19785": [-117.1585, 32.7195], "19905": [-122.0825, 47.4895], "19907": [-71.6025, 42.7605], "19908": [-93.1625, 45.0515], "19912": [-93.2025, 45.0785], "19946": [-122.0805, 37.3905], "19952": [-71.2405, 42.4085], "19955": [-73.2005, 42.4795], "19956": [-122.0205, 37.3905], "19957": [-112.0305, 46.6005], "19960": [-86.1595, 39.7675], "19963": [-98.4395, 29.5285], "19966": [-71.3795, 42.9405], "19976": [-111.6895, 40.2805], "19998": [-89.3685, 43.0815], "20105": [-83.7525, 42.2795], "20182": [-105.0785, 40.5885], "20188": [-89.4085, 43.0715], "20282": [-122.8885, 45.5085], "20431": [-121.9215, 37.2875], "20435": [-80.3615, 27.6495], "20436": [-121.8115, 36.6505], "20453": [-77.7105, 39.1285], "20470": [-81.6195, 35.7075], "20493": [-72.2785, 42.9285], "20614": [-95.4625, 30.3095], "20625": [-73.9415, 40.8295], "20639": [-83.4915, 42.3815], "20683": [-75.0685, 38.6885], "20687": [-74.3485, 40.6405], "20689": [-74.2485, 40.4315], "20734": [-92.4315, 34.6595], "20740": [-121.8905, 37.3275], "20753": [-85.3305, 42.2385], "20756": [-114.2805, 48.2205], "20778": [-83.3295, 33.1615], "20781": [-75.1885, 39.9375], "20793": [-122.1185, 37.4185], "20794": [-71.5385, 42.3095], "20813": [-97.0025, 37.9985], "20913": [-73.3325, 40.9185], "21000": [-122.3425, 47.6075], "21003": [-120.6025, 46.6685], "21023": [-122.3015, 47.5585], "21028": [-121.9115, 36.9715], "21030": [-93.2515, 44.9975], "21031": [-108.5815, 45.7975], "21074": [-75.5395, 40.1795], "21087": [-122.2385, 37.4705], "21119": [-77.0325, 39.0015], "21133": [-72.3115, 42.9585], "21152": [-93.1305, 45.0685], "21378": [-71.1495, 42.2315], "21675": [-104.8995, 39.5295], "21700": [-79.9025, 37.2975], "21761": [-75.5995, 39.7375], "21791": [-89.4085, 43.0675], "21802": [-122.3525, 47.6185], "21806": [-121.9425, 37.7005], "21863": [-122.2595, 45.3985], "21865": [-122.3195, 37.5695], "21885": [-90.2485, 38.6395], "21905": [-88.4425, 41.7595], "22129": [-80.8015, 41.8615], "22199": [-105.2985, 40.0415], "22288": [-84.3885, 33.7815], "22379": [-121.8895, 37.3415], "22382": [-77.3985, 38.8585], "22396": [-105.1585, 39.9805], "22442": [-82.9805, 35.5285], "22444": [-157.8205, 21.2995], "22446": [-72.6505, 44.3405], "22447": [-122.4205, 37.7705], "22511": [-78.8225, 35.6075], "22530": [-155.4715, 19.8175], "22596": [-118.4285, 34.1405], "22604": [-122.0825, 47.7395], "22611": [-76.7125, 39.2575], "22619": [-88.5425, 44.0315], "22675": [-122.2895, 47.4895], "22696": [-118.3885, 33.8605], "22709": [-71.4725, 42.7715], "22710": [-118.4525, 34.0375], "22715": [-122.0325, 37.3795], "22720": [-75.8815, 39.7675], "22723": [-73.7415, 41.6685], "22731": [-122.2815, 47.3275], "22764": [-122.8795, 42.2995], "22797": [-76.4985, 39.0305], "22802": [-105.2225, 39.7485], "22814": [-121.9525, 37.8395], "22853": [-122.1205, 47.6685], "22869": [-73.9995, 40.7415], "22870": [-122.3895, 37.7875], "22881": [-77.3885, 38.9675], "23005": [-78.5825, 38.0595], "23017": [-96.7125, 32.9805], "23033": [-117.1615, 32.7085], "23036": [-74.0015, 40.7405], "23074": [-80.1195, 26.8595], "23077": [-80.1595, 26.5705], "23108": [-75.1725, 39.9515], "23133": [-82.4715, 28.0685], "23704": [-77.0425, 38.8995], "23840": [-71.3705, 41.8075], "23841": [-77.8705, 40.8075], "23956": [-90.2505, 38.6405], "23978": [-90.2495, 38.6415], "23979": [-75.1995, 39.9615], "23984": [-90.2485, 38.6295], "23993": [-80.2085, 25.7885], "24191": [-90.2485, 38.6375], "24245": [-117.0705, 32.7695], "24247": [-80.2105, 25.7905], "24303": [-97.5725, 35.3485], "24633": [-95.8415, 41.2585], "24639": [-69.0915, 44.2115], "24680": [-121.9685, 36.9775], "24725": [-77.3015, 38.9495], "24899": [-84.7785, 45.0415], "24908": [-124.4225, 43.0515], "24940": [-80.9005, 34.9875], "24971": [-105.2195, 39.7475], "24994": [-90.0685, 29.9495], "24998": [-121.2585, 38.6815], "25027": [-90.9915, 30.3505], "25060": [-104.7895, 39.5875], "25069": [-72.2995, 43.7615], "25081": [-73.9485, 40.7875], "25191": [-93.3185, 37.0575], "25206": [-94.8325, 39.1605], "25224": [-96.8115, 46.8195], "25232": [-122.4015, 37.7885], "25324": [-81.7815, 24.5595], "25390": [-96.1885, 48.0975], "25393": [-121.9585, 37.3885], "25724": [-84.3315, 33.8295], "25737": [-93.1815, 44.9505], "25764": [-121.9895, 37.3595], "25776": [-73.1395, 40.9305], "25784": [-94.3285, 38.8995], "25798": [-115.2785, 36.1715], "25850": [-88.2505, 40.1075], "25854": [-88.1005, 40.4595], "25860": [-118.4495, 33.9775], "25925": [-87.6615, 40.4595], "25953": [-93.2705, 44.9785], "25982": [-96.8885, 32.9785], "25988": [-88.1985, 40.1015], "26056": [-122.7705, 48.9005], "26143": [-86.1105, 40.4685], "26147": [-122.0205, 37.2705], "26153": [-74.0105, 40.7085], "26250": [-115.0305, 36.0375], "26449": [-117.2005, 32.8515], "26496": [-71.1685, 42.2905], "26518": [-77.5925, 43.0715], "26564": [-118.3795, 34.0495], "26707": [-111.6825, 40.0105], "26758": [-111.9205, 40.6115], "26862": [-93.7095, 41.7685], "26863": [-77.4295, 39.3785], "26934": [-77.5215, 39.0495], "26946": [-84.2805, 30.4405], "26956": [-83.6305, 41.5205], "27020": [-77.5815, 43.1575], "27148": [-122.0605, 37.4215], "27195": [-110.8885, 32.2095], "27214": [-95.4525, 30.0595], "27245": [-120.8705, 37.5995], "27283": [-93.4685, 41.6385], "27310": [-96.0725, 41.1275], "27362": [-122.2695, 37.8885], "27667": [-93.2795, 44.9905], "27727": [-112.1015, 33.3905], "27728": [-75.1015, 39.7115], "27739": [-74.6515, 40.3215], "27757": [-121.7905, 36.6805], "27761": [-118.5395, 34.1975], "27780": [-73.9885, 40.6575], "27798": [-112.3585, 33.4915], "27884": [-78.5585, 38.1495], "27899": [-71.1185, 42.4015], "28118": [-78.5625, 38.1515], "28154": [-74.7905, 40.2595], "28179": [-105.1495, 39.9215], "28181": [-92.1185, 34.7375], "28204": [-70.8625, 43.2695], "28221": [-111.8315, 40.5275], "28225": [-93.0115, 45.0895], "28255": [-71.3705, 42.9395], "28314": [-71.8825, 42.7395], "28321": [-84.4515, 39.3675], "28507": [-118.4025, 34.2605], "28511": [-122.3525, 47.6175], "28529": [-122.4215, 37.7715], "28537": [-76.6215, 39.1605], "28539": [-110.9315, 32.2415], "28541": [-122.3005, 37.8675], "28592": [-112.0485, 33.0585], "28597": [-117.0685, 33.0005], "28600": [-122.3325, 47.6075], "28639": [-83.0615, 39.9915], "28659": [-76.3305, 40.0115], "28670": [-73.9995, 40.7375], "28676": [-122.1695, 47.5505], "28677": [-104.8795, 39.8905], "28684": [-77.0885, 38.9795], "28687": [-120.5485, 43.8005], "28691": [-77.4885, 39.0375], "28710": [-122.1625, 38.0475], "28720": [-76.1515, 43.0475], "28734": [-77.1115, 38.8795], "28794": [-76.9885, 38.8995], "28834": [-122.0315, 37.3195], "28864": [-77.4595, 39.0195], "29000": [-75.1925, 39.9475], "29004": [-88.0025, 42.0495], "29006": [-71.2225, 42.4505], "29049": [-91.0005, 30.3615], "29062": [-122.0495, 37.9585], "29078": [-121.9495, 37.4015], "29112": [-78.0225, 41.7685], "29128": [-122.0415, 37.3715], "29138": [-80.4315, 37.2715], "29242": [-90.4605, 38.4585], "29287": [-122.5185, 47.6205], "29295": [-78.6185, 35.8095], "29338": [-122.3315, 47.6115], "29383": [-77.1885, 39.2585], "30249": [-122.6305, 45.4715], "30253": [-82.4105, 28.0585], "30256": [-73.9805, 40.6905], "30260": [-122.3295, 47.6075], "30261": [-71.4395, 42.5775], "30263": [-99.4795, 27.5285], "30275": [-83.9195, 35.9595], "30303": [-95.3725, 30.0985], "30350": [-122.6605, 45.3575], "30352": [-121.9605, 37.2385], "30383": [-88.5385, 44.0285], "30432": [-76.3115, 40.1685], "30437": [-122.6715, 38.4305], "30456": [-73.9705, 40.6905], "30512": [-95.9325, 41.2585], "30522": [-122.6515, 45.5285], "30537": [-122.0715, 37.4305], "30561": [-72.4995, 43.3175], "30582": [-122.7985, 38.3385], "30595": [-122.6285, 38.2195], "30599": [-97.3085, 32.9315], "30680": [-77.4085, 37.2475], "30779": [-71.0795, 42.3815], "30797": [-76.9885, 39.1105], "31113": [-122.2025, 47.6085], "31116": [-111.8925, 33.4005], "31121": [-122.6615, 45.0675], "31128": [-70.6815, 44.2015], "31134": [-71.6015, 42.1695], "31142": [-119.2205, 34.2985], "31160": [-119.2695, 34.2675], "31165": [-81.4695, 41.5095], "31169": [-120.1195, 39.2815], "31174": [-114.0795, 48.0395], "31181": [-77.3685, 38.8975], "31183": [-122.1985, 47.6185], "31208": [-74.0025, 40.7415], "31209": [-73.9825, 40.6715], "31224": [-105.0115, 40.1995], "31246": [-96.8405, 32.8005], "31250": [-77.3405, 38.9475], "31253": [-82.7805, 39.8685], "31255": [-118.2405, 34.0495], "31293": [-93.2285, 44.9485], "31304": [-117.1625, 33.5695], "31313": [-117.7925, 33.8485], "31318": [-84.5825, 42.7115], "31330": [-77.1115, 38.8875], "31332": [-118.4415, 33.9785], "31386": [-122.4185, 37.7505], "31389": [-77.3085, 38.7915], "31390": [-71.2185, 42.4475], "31393": [-73.6185, 42.8085], "31398": [-78.8785, 35.8315], "31423": [-122.0615, 37.3785], "31492": [-91.6385, 41.8485], "31515": [-85.2725, 36.1495], "31519": [-73.9625, 40.6815], "31536": [-75.8615, 39.8005], "31559": [-82.4905, 40.0415], "31690": [-75.5385, 42.8275], "31775": [-97.7495, 30.2795], "31904": [-81.4625, 41.5295], "32122": [-118.2715, 33.9685], "32155": [-69.9705, 43.9095], "32186": [-82.5085, 40.3305], "32259": [-81.3905, 28.6215], "32262": [-118.2595, 34.0485], "32316": [-87.8325, 42.1305], "32324": [-78.6415, 35.7795], "32334": [-76.2615, 42.0995], "32383": [-77.0185, 38.8785], "32421": [-85.2415, 38.2275], "32462": [-113.7895, 42.4985], "32471": [-87.6895, 42.0475], "32488": [-96.0485, 41.2315], "32512": [-76.4125, 39.5085], "32545": [-74.0405, 40.7395], "32555": [-87.6305, 41.8795], "32567": [-118.4095, 34.0205], "32572": [-105.0195, 39.9185], "32574": [-104.7295, 39.5995], "32580": [-74.1185, 40.7475], "32585": [-122.4385, 37.7495], "32592": [-73.9385, 42.8085], "32593": [-106.6485, 35.0985], "32595": [-77.4585, 41.1395], "32604": [-122.5425, 47.6495], "32613": [-74.0025, 40.7385], "32616": [-122.5625, 45.6405], "32643": [-105.8505, 35.6185], "32660": [-94.4695, 39.1675], "32710": [-77.6125, 38.2075], "32788": [-78.7885, 35.7315], "32826": [-84.3915, 33.7805], "32827": [-71.0515, 42.4605], "32849": [-119.7205, 39.0415], "32853": [-96.7405, 33.1685], "32933": [-122.4415, 37.6385], "33004": [-73.8525, 40.7195], "33030": [-105.0815, 40.5875], "33036": [-122.0615, 36.9905], "33037": [-97.8415, 30.2005], "33045": [-105.1005, 40.5795], "33056": [-104.7205, 39.6205], "33062": [-106.5895, 35.0985], "33065": [-71.4495, 41.4495], "33067": [-121.9995, 37.3705], "33068": [-83.9495, 43.4215], "33076": [-112.0695, 33.4505], "33080": [-96.6385, 40.7775], "33081": [-70.0985, 43.8575], "33086": [-75.2385, 40.6705], "33109": [-122.3325, 47.6115], "33129": [-81.4415, 41.1615], "33139": [-111.6515, 40.2515], "33170": [-71.0895, 42.3575], "33184": [-76.0485, 41.3495], "33193": [-74.0785, 40.7285], "33262": [-123.1095, 44.6385], "33297": [-78.9085, 35.8505], "33316": [-84.5825, 37.8805], "33415": [-77.0525, 38.7995], "33418": [-105.2625, 40.0115], "33435": [-82.7715, 27.9995], "33492": [-86.9085, 40.4185], "33495": [-74.6585, 40.5795], "33500": [-122.4125, 37.7875], "33502": [-93.4625, 45.0685], "33609": [-79.2625, 37.3915], "33640": [-74.0305, 40.7375], "33642": [-85.0805, 35.0685], "33643": [-121.4905, 38.6485], "33644": [-77.3605, 38.8995], "33646": [-77.5705, 37.5005], "33655": [-78.5805, 38.0595], "33673": [-80.5795, 37.1285], "33699": [-71.7985, 42.5815], "33702": [-70.8925, 42.5285], "33705": [-73.9025, 40.7695], "33712": [-89.4725, 43.0585], "33713": [-104.9925, 39.9085], "33715": [-78.7825, 35.9195], "33740": [-78.9405, 35.7875], "33759": [-116.5705, 47.3215], "33798": [-122.3085, 47.7015], "33882": [-122.2985, 47.6285], "33897": [-122.0285, 36.9705], "34084": [-97.8185, 30.4395], "34087": [-118.3885, 33.9505], "34089": [-122.2285, 47.3815], "34100": [-122.3925, 47.5375], "34113": [-72.2525, 43.6385], "34156": [-84.3905, 33.7505], "34164": [-86.2595, 40.2995], "34166": [-104.7295, 39.5005], "34176": [-84.5695, 42.7405], "34180": [-122.4185, 37.7575], "34203": [-91.2025, 43.4185], "34231": [-86.9115, 40.4275], "34234": [-118.4515, 34.0395], "34246": [-83.3905, 33.9205], "34261": [-84.3895, 33.7475], "34271": [-69.2895, 44.8375], "34275": [-77.5595, 39.1195], "34287": [-87.6285, 41.8805], "34291": [-84.3385, 33.7175], "34297": [-72.5185, 42.3705], "34311": [-96.8825, 33.0675], "34313": [-97.6425, 35.5585], "34318": [-97.7225, 30.4015], "34334": [-95.6615, 29.8995], "34355": [-90.5605, 30.0695], "34359": [-97.8205, 37.7515], "34514": [-93.2325, 41.5995], "34614": [-78.7825, 35.7895], "34631": [-98.3315, 29.5875], "34652": [-87.5205, 41.4885], "34655": [-83.5305, 43.0195], "34658": [-104.9405, 39.9415], "34661": [-81.3395, 28.6975], "34680": [-72.8685, 41.3175], "34681": [-71.0585, 42.4575], "34682": [-83.9985, 34.1085], "34691": [-95.5385, 29.7775], "34710": [-92.1025, 46.7875], "34723": [-88.2715, 34.8185], "34726": [-88.3115, 44.2305], "34728": [-93.6915, 32.5815], "34732": [-96.2915, 30.5785], "34734": [-84.2215, 39.3895], "34739": [-76.4715, 37.0615], "34742": [-121.9205, 37.4685], "34747": [-122.2105, 47.7605], "34754": [-86.7505, 34.6995], "34756": [-78.7905, 35.9105], "34759": [-122.0505, 47.5415], "34762": [-95.2995, 32.3485], "34765": [-118.3995, 34.0195], "34770": [-111.9795, 33.3175], "34779": [-95.1795, 30.0015], "34780": [-111.8385, 33.3075], "34788": [-90.3785, 38.4915], "34790": [-104.7585, 39.7975], "34804": [-122.4125, 37.7995], "34838": [-72.5215, 41.7815], "34860": [-122.3295, 47.6075], "34874": [-82.5295, 27.8795], "34881": [-77.3585, 39.0275], "35001": [-93.2025, 30.1975], "35031": [-80.2415, 26.2875], "35032": [-81.5915, 41.4885], "35045": [-84.3905, 33.7795], "35052": [-117.1205, 33.5085], "35056": [-118.4005, 34.0705], "35064": [-75.3095, 39.9795], "35065": [-75.5195, 39.1595], "35066": [-106.2195, 35.8205], "35070": [-84.0295, 35.0875], "35071": [-104.8895, 39.6175], "35073": [-83.1595, 42.4985], "35076": [-73.9695, 40.7905], "35079": [-111.6795, 33.2715], "35081": [-93.4485, 44.8575], "35092": [-89.0085, 42.4085], "35093": [-121.9185, 37.4685], "35103": [-71.0525, 42.4585], "35105": [-121.9425, 37.5495], "35109": [-81.7825, 32.4515], "35123": [-80.7215, 35.1185], "35140": [-104.7605, 41.1375], "35146": [-118.3905, 34.0205], "35151": [-119.5505, 47.3175], "35207": [-89.4025, 43.0705], "35221": [-96.7815, 32.9875], "35228": [-74.4015, 40.3915], "35259": [-80.7705, 35.1315], "35269": [-80.7795, 37.0515], "35279": [-88.2395, 40.1215], "35283": [-84.5685, 34.0385], "35289": [-96.4985, 33.1715], "35296": [-83.7285, 42.8005], "35415": [-95.9425, 36.1495], "35465": [-84.3395, 33.8695], "35498": [-122.3985, 47.5715], "35500": [-122.3025, 40.4475], "35553": [-80.6605, 35.1685], "35557": [-80.2205, 40.6205], "35561": [-82.8095, 39.9975], "35592": [-74.0785, 40.7285], "35596": [-80.3385, 37.1105], "35620": [-101.8615, 33.5775], "35628": [-80.3015, 36.1315], "35640": [-77.0705, 38.9475], "35673": [-87.7495, 41.9685], "35726": [-83.9615, 42.0505], "50017": [-77.9625, 39.1005], "50117": [-77.4025, 39.0405], "50147": [-122.4205, 37.6505], "50164": [-77.4095, 38.8495], "50172": [-86.5795, 34.6085], "50268": [-87.9195, 42.5615], "50375": [-105.1195, 39.8795], "50456": [-96.8105, 33.0805]}
    
    def get_inp_4_baidu_map(self, list_pid):
        map_pid2coordinate = {}
        list_name_value = []
        for pid in pyprind.prog_bar(list_pid):
            probe_info = self.get_probe_info(pid)
            map_pid2coordinate[pid] = [probe_info["longitude"], probe_info["latitude"]]
            list_name_value.append({"name": pid, "value": 50})
    
        print(list_name_value)
        print("---------------------------------")
        print(map_pid2coordinate)


if __name__ == "__main__":
    import pytz
    zone = pytz.country_timezones('us')[0]
    tz = pytz.timezone(zone)
    start_time = datetime.datetime.now(tz).timestamp() + 120

    list_pid = ["34759", "33759", "21031", "25224", "24899", "15760", "24908", "32462", "24971", "24633", "35561", "10599", "30352", "11634", "35620", "35415", "12180", "2427", "16951", "12105", "30263", "35001", "26946", "24247"]
    account_key = settings.RIPE_ACCOUNT_KEY[1]
    ripe = RipeAtlas(account_key["account"], account_key["key"])

    map_ip_coord = ripe.get_all_probes_us("../Sources/landmarks_ripe_us.json")
    # json.dump(map_ip_coord, open("../Sources/landmarks_ripe_us.json", "w"))

    list_target = [ip for ip in map_ip_coord.keys()]
    # list_target = list_target[:1000] if len(list_target) > 1000 else list_target
    list_target = list_target[500:]
    ripe.measure_by_ripe_hugenum_oneoff_traceroute(list_target, list_pid, start_time,
                                      ["ipg-22018111701", ], "test: 24 * 400+（500：~）",)


