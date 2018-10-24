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
import pyprind

# def traceroute_query(location, hostname):
#     url = "https://tools.keycdn.com/traceroute"
#     headers = rt.get_random_headers()
#     # headers["origin"] = "https://tools.keycdn.com"
#     # headers["referer"] = "www.google.com"
#     headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
#     # headers["cookie"] = "_ga=GA1.2.50660787.1539681526; PHPSESSID=n1b9ha7vj6clfbuv10u27dhmo9; _gid=GA1.2.1704225776.1540180890; keycdn=kd58cb91ua9nbb9ktevbtirhmp5lodte"
#     # headers["accept-encoding"] = "gzip, deflate, br"
#     # headers["accept-language"] = "zh-CN,zh;q=0.9,en;q=0.8"
#     headers["content-type"] = "application/x-www-form-urlencoded; charset=UTF-8"
#     # headers["content-length"] = "101"
#     headers["x-requested-with"] = "XMLHttpRequest"
#     proxies = rt.get_proxies_abroad()
#
#     session = requests.session()
#     session.get("https://www.keycdn.com")
#     session.get("https://tools.keycdn.com", proxies=proxies,)
#     res = session.get(url, headers=headers, proxies=proxies, timeout=10)
#     search_group = re.search("token=([0-9a-z]+)", res.text)
#     token = None
#     if search_group:
#         token = search_group.group(1)
#
#     api = "https://tools.keycdn.com/trace-query.php"
#     data = {
#         "location": location,
#         "hostname": hostname,
#         "token": token,
#     }
#     res = session.post(api, data=data, proxies=proxies, timeout=10)
#     return res.text
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


if __name__ == "__main__":
    chrome = init_chrome()
    chrome.get("https://tools.keycdn.com/traceroute")

    json_landmarks = json.load(open("../sources/landmarks_planet_lab_us.json", "r"))
    for lm in pyprind.prog_bar(json_landmarks):
        ip = lm["ip"]
        t1 = time.time()
        res = trace_route_query(chrome, ip)
        lm["measurement_keycdn"] = [res, ]
        print(res)
        t2 = time.time()
        print(t2 - t1)

    json.dump(json_landmarks, open("../sources/landmarks_planetlab_us_measured.json", "w"))

