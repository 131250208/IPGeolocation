from Tools import mylogger
from bs4 import BeautifulSoup
import json
import re
from LandmarksCollector import owner_name_extractor, iterative_inference_machine
import enumeration
from Tools import geoloc_commercial_db, purifier, geo_distance_calculator, network_measurer
import settings
import logging
logger = mylogger.Logger("../Log/data_preprocessor.py.log", clevel=logging.INFO)
import time
import random
import pytz
import datetime
import pyprind
import strings
import numpy as np
from itertools import combinations
# from sklearn.preprocessing import scale


# def is_valid(line):
#     '''
#     check:
#         not "\n",
#         can be loaded by json,
#         not error page,
#         has status_code and it is 200
#
#     :param line: a line of bytes read from file
#     :return: boolen
#     '''
#
#     line = line.decode("utf-8")
#
#     if line.strip("\n") == "":
#         return False
#
#     # filter json loading fail
#     try:
#         banner_info = json.loads(line)
#     except Exception as e:
#         logger.war(e)
#         logger.war("error str can not be loads as json: %s" % line)
#         return False
#
#     if "error" in banner_info:  # filter error pages
#         return False
#
#     # filter samples without status code
#     try:
#         status_code = banner_info["data"]["http"]["response"]["status_code"]
#     except Exception as e:
#         logger.war(e)
#         logger.war("has no status_code: %s" % line)
#         return False
#
#     if status_code != 200:  # filter pages of which status code is not 200
#         return False
#     return True


def get_brief_one(line):
    '''
    get brief info from line, including:
        "title": title,
        "url": "%s://%s%s" % (scheme, host, path),
        "html": html,
        "ip": ip,
        "host": "%s://%s" % (scheme, host),
    :param line:
    :return:
            None:
                can not be loaded by json
                if no url(scheme, host, path) in sample

            Else:
                a dict including "title", "url", "html", "ip", "host"
            FYI, sometimes title can be "".
    '''
    try:
        banner_info = json.loads(line.decode("utf-8"))
    except Exception as e:
        logger.war(e)
        return None

    ip = banner_info["ip"]
    response = banner_info["data"]["http"]["response"]
    if "body" in response:
        html = response["body"]
    else:
        return None

    if html.strip() == "":
        return None

    title = ""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return None

    tag_title = soup.select_one("title")
    if tag_title is not None:
        title = tag_title.get_text()
    else:
        match = re.search("<title[^>]*>(.*)</title>", html)
        if match is not None:
            title = match.group(1)

    try:
        url = response["request"]["url"]
        scheme = ""
        host = ""
        path = ""
        if "scheme" in url:
            scheme = url["scheme"]
        if "host" in url:
            host = url["host"]
        if "path" in url:
            path = url["path"]

        return {"title": title,
                "url": "%s://%s%s" % (scheme, host, path),
                "html": html,
                "ip": ip,
                "scheme": scheme,
                "host": host,
                "path": path,
                }
    except Exception as e:
        logger.war(e)
        return None


def check_title(title):
    for w in settings.BlACK_LIST_INVALID_PAGE:
        if w.lower() in title.lower():
            return False
    return True


def is_valid(sample):
    if "error" in sample:  # filter error pages
        return False

    # filter out samples without status code
    try:
        status_code = sample["data"]["http"]["response"]["status_code"]
    except Exception as e:
        return False

    if status_code != 200:  # filter out pages of which status code is not 200
        return False
    return True


def filter_out_unnecessary_info(sample):
    '''
    only remain the necessary info for recognition
    :param sample:
    :return:
    '''
    ip = sample["ip"]
    response = sample["data"]["http"]["response"]

    if "body" in response:
        html = response["body"]
    else:
        return None

    if html.strip() == "":
        return None

    title = ""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return None

    tag_title = soup.select_one("title")
    if tag_title is not None:
        title = tag_title.get_text()
    else:
        match = re.search("<title[^>]*>(.*)</title>", html)
        if match is not None:
            title = match.group(1)

    try:
        url = response["request"]["url"]
        scheme = ""
        host = ""
        path = ""
        if "scheme" in url:
            scheme = url["scheme"]
        if "host" in url:
            host = url["host"]
        if "path" in url:
            path = url["path"]

        return {"title": title,
                "url": "%s://%s%s" % (scheme, host, path),
                "html": html,
                "ip": ip,
                "scheme": scheme,
                "host": host,
                "path": path,
                }
    except Exception as e:
        logger.war(e)
        return None
# --------------------------------batch processing---------------------------------------------------------------------


def filter_ips_in_us(samples, *args):
    new_samples = []
    for sample in samples:
        locs = geoloc_commercial_db.get_locations_info_by_commercial_tools(sample["ip"])
        in_us = True
        for loc in locs:
            if loc["country"] != "United States" and loc["country"] != "美国":
                in_us = False

        if in_us:
            new_samples.append(sample)

    return new_samples


def filter_out_duplicates_n_invalid_samples(samples, *args):
    '''
    filter out invalid(dead) IPs and duplicates
    :param samples:
    :param args:
    :return:
    '''
    set_ip = args[0]
    new_samples = []
    for sample in samples:
        if is_valid(sample) and sample["ip"] not in set_ip:
            sample = filter_out_unnecessary_info(sample)
            if sample is not None:
                set_ip.add(sample["ip"])
                new_samples.append(sample)
    return new_samples


def extract_org_names(samples, *args):
    org_name_dict = args[0]
    for sample in samples:
        # org_names = []
        # if strings.KEY_POTENTIAL_OWNER_NAMES in sample:
        #     org_names = sample[strings.KEY_POTENTIAL_OWNER_NAMES]
        # else:
        org_names = owner_name_extractor.extract_org_names_fr_page(sample["html"], org_name_dict)
        org_names.append(owner_name_extractor.get_org_name_by_registration_db(sample["ip"]))

        # filer out duplicates
        org_names = sorted(org_names, key=lambda x: len(x), reverse=True)
        org_names_new = []
        mem = ""
        for s in org_names:
            if s.lower() not in mem.lower():
                org_names_new.append(s)
                mem += " %s" % s
        org_names = org_names_new

        sample[strings.KEY_POTENTIAL_OWNER_NAMES] = org_names
        print("{:.1f} {} {}".format(sample["dis_coarse_2_ground"] / 1000, sample["organization"], sample[strings.KEY_POTENTIAL_OWNER_NAMES]))

    return samples


def find_pages_with_copyright(in_file_path, out_file_path, index):
    '''
    find samples with copyright on its page
    :param in_file_path:
    :param out_file_path:
    :param index:
    :return:
    '''
    f_inp = open(in_file_path, "r", encoding="utf-8")
    f_out = open(out_file_path, "a", encoding="utf-8")

    ind = 0
    count = 0
    for line in f_inp:
        if ind < index or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % (ind))
            ind += 1
            continue
        try:
            sample = json.loads(line)
        except Exception:
            continue

        html = sample["html"]
        soup = purifier.get_pure_soup_fr_html(html)

        org_fr_copyright = owner_name_extractor.extract_org_fr_copyright(soup)

        if len(org_fr_copyright) > 0:
            f_out.write("%s\n" % json.dumps(sample))
            count += 1
            logger.war("----------count: %d-------ind: %d identification: %s--------------------" % (count, ind, True))
        else:
            print("--------count: %d---------ind: %d identification: %s--------------------" % (count, ind, False))
        ind += 1

    f_out.close()


def incorporate_coarse_locations_fr_commercial_dbs(samples, *args):
    for sample in samples:
        ip = sample["ip"]
        ipinfo_fr_commercial_tools = geoloc_commercial_db.get_locations_info_by_commercial_tools(ip)
        sample[strings.KEY_LOCS_FROM_COMMERCIAL_TOOLS] = ipinfo_fr_commercial_tools
    return samples


# def incorporate_coordinate_fr_commercial_db(in_file_path, out_file_path, index):
#     '''
#     filter out IPs of which the location is ambiguous, that is, whose results from commercial databases are very different
#     '''
#
#     f_inp = open(in_file_path, "r", encoding="utf-8")
#     f_out = open(out_file_path, "a", encoding="utf-8")
#     ind = 0
#     for line in f_inp:
#         if ind < index or line.strip() == "\n":
#             print("-----------------ind: %d pass--------------------" % ind)
#             ind += 1
#             continue
#         try:
#             sample = json.loads(line)
#         except Exception:
#             continue
#
#         print("-----------------ind: %d-------------------" % ind)
#
#         ip = sample["ip"]
#         ipinfo_fr_commercial_tools = geoloc_commercial_db.get_location_info_by_commercial_tools_unanimous(ip) # filter
#
#         if ipinfo_fr_commercial_tools is None:
#             ind += 1
#             print("%s the city is ambiguous..." % ip)
#             continue
#
#         sample["result_fr_commercial_tool"] = ipinfo_fr_commercial_tools
#         f_out.write("%s\n" % json.dumps(sample))
#
#         ind += 1
#
#     f_out.close()


def incorporate_candidates_fr_web_mapping_services(samples, *args):
    radius = args[0]

    new_samples = []
    for sample in samples:
        t1 = time.time()
        sample = iterative_inference_machine.search_candidates(sample, radius)
        new_samples.append(sample)
        t2 = time.time()
        print(t2 - t1)
    return new_samples


def choose_obsevers(observers):
    len_ori_obs = len(observers)
    dis_matrix = list(np.ones([len_ori_obs, len_ori_obs], dtype=float).tolist())
    for ind1, ob1 in enumerate(observers.values()):
        for ind2, ob2 in enumerate(observers.values()):
            dis = geo_distance_calculator.get_geodistance_btw_2coordinates(ob1["longitude"], ob1["latitude"], ob2["longitude"], ob2["latitude"])
            dis_matrix[ind1][ind2] = dis

    np.array(dis_matrix)
    score_list = []
    for ind, ob in enumerate(observers.values()):
        score = 1
        for dis in dis_matrix[ind]:
            score *= (dis + 0.1)
        score_list.append(score)

    temp_bound = zip(observers, score_list)
    sorted(temp_bound, key=lambda x: x[1], reverse=True)
    observers_ordered, scores = zip(*temp_bound)

    return observers_ordered[:25]


def incorporate_observers_n_landmarks(samples, *args):
    ripe_account = settings.RIPE_ACCOUNT_KEY[0]
    ripe = network_measurer.RipeAtlas(ripe_account["account"], ripe_account["key"])
    ip_2_loc_ripe = ripe.get_all_probes_us("../Sources/landmarks_ripe_us.json")
    ip_2_loc_existing_landmarks = json.load(open("../Sources/landmarks/landmarks_fr_cyberspace_2.json", "r", encoding="utf-8"))

    for sample in samples:
        observers = {}
        landmarks = {}
        coarse_locs = geo_distance_calculator.merge_near_locations(sample[strings.KEY_LOCS_FROM_COMMERCIAL_TOOLS], 20000)
        for loc in coarse_locs:
            for ip, lm in ip_2_loc_existing_landmarks.items():
                dis = geo_distance_calculator.get_geodistance_btw_2coordinates(loc["longitude"], loc["latitude"], lm["longitude"], lm["latitude"])
                if dis < settings.RADIUS_FOR_SEARCHING_CANDIDATES:
                    landmarks[ip] = lm
            for ip, ob in ip_2_loc_ripe.items():
                dis = geo_distance_calculator.get_geodistance_btw_2coordinates(loc["longitude"], loc["latitude"], ob["longitude"], ob["latitude"])
                if dis < settings.RADIUS_FOR_SEARCHING_CANDIDATES:
                    observers[ip] = ob

        # if len(observers) > 25:
        #     observers = choose_obsevers(observers)

        sample[strings.KEY_PROBES_4_INFERENCE] = observers
        sample[strings.KEY_LANDMARKS_4_INFERENCE] = landmarks

    return samples


def merge_near_candidates(samples):
    for sample in pyprind.prog_bar(samples):
        candidates = sample[strings.KEY_CANDIDATES]
        candidates = iterative_inference_machine.merge_near_candidates(candidates, settings.MAX_DIS_WITHIN_A_SINGLE_ORG)
        sample[strings.KEY_MERGED_CANDIDATES] = candidates

        if len(candidates) == 1:
            sample[strings.KEY_STATUS] = enumeration.SAMPLE_STATUS_FIN
            sample[strings.KEY_ESTIMATED_COORDINATE] = candidates[0]
        elif len(candidates) > 1:
            sample[strings.KEY_STATUS] = enumeration.SAMPLE_STATUS_WFVG
        else:
            sample[strings.KEY_STATUS] = enumeration.SAMPLE_STATUS_FAI
    return samples


def slice_sample_file_by_num_of_candidates(inp_file_path, out_directory, index_start):
    f_inp = open(inp_file_path, "r", encoding="utf-8")

    ind = 0
    for line in f_inp:
        print("--------------ind: %d--------------" % ind)
        if ind < index_start or line.strip() == "\n":
            print("-----------------ind: %d pass-------------" % ind)
            ind += 1
            continue

        try:
            sample = json.loads(line.strip("\n"))
        except Exception:
            continue

        candidates = sample["candidates_merged"]
        num_can = len(candidates)
        if num_can > 0:
            f_out = open("%s/sample_us_with_%d_candidates.json" % (out_directory, num_can), "a", encoding="utf-8")
            f_out.write("%s\n" % json.dumps(sample))
            f_out.close()
        ind += 1


def get_initial_landmarks(inp_path):
    file = open(inp_path, "r")
    sample_list = []

    dict_landmarks_total = {}
    for line in file:
        sample = json.loads(line.strip("\n"))
        sample_list.append(sample)

        if len(sample_list) == 10000:
            dict_landmarks = iterative_inference_machine.generate_initail_landmarks(sample_list)
            len_lm = len(list(dict_landmarks.keys()))
            dict_landmarks_total = {**dict_landmarks, **dict_landmarks_total}
            print(len_lm)
            sample_list.clear()

    dict_landmarks = iterative_inference_machine.generate_initail_landmarks(sample_list)
    len_lm = len(list(dict_landmarks.keys()))
    print(len_lm)
    dict_landmarks_total = {**dict_landmarks, **dict_landmarks_total}

    count_landmarks = len(dict_landmarks_total)
    print("total: %d" % count_landmarks)
    return dict_landmarks_total


def check_landmarks(dict_landmarks):
    dict_landmarks_filtered = {}

    count = 0
    for key, val in dict_landmarks.items():
        if network_measurer.ping(key, 1):
            dict_landmarks_filtered[key] = val
        count += 1
        logger.info("--------------------%d-------------------" % count)
    return dict_landmarks_filtered


def match_guards_to_candidates(in_file_path, out_file_path, index_start):
    f_inp = open(in_file_path, "r", encoding="utf-8")
    f_out = open(out_file_path, "a", encoding="utf-8")

    dict_landmarks = json.load(open("../Sources/landmarks_fr_cyberspace_2.json", "r"))
    dict_landmarks = check_landmarks(dict_landmarks)

    ind = 0
    for line in f_inp:
        print("-------------ind: %d------------" % ind)
        if ind < index_start or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue

        try:
            sample = json.loads(line.strip("\n"))
        except Exception:
            continue

        sample = iterative_inference_machine.match_guard_to_candidates(sample, dict_landmarks, 2000)
        f_out.write("%s\n" % json.dumps(sample))
        ind += 1
    f_out.close()


def get_measurment_tasks_for_inference(in_file_path, index_start):
    f_inp = open(in_file_path, "r", encoding="utf-8")
    ind = 0
    probes = json.load(open("../Sources/landmarks_ripe_us_2.json", "r"))
    probe_list = [{"id": val["id"], "longitude": val["longitude"], "latitude": val["latitude"]} for key, val in probes.items()]
    count = 0

    task_list = []
    for line in f_inp:
        print("-------------ind: %d------------" % ind)
        if ind < index_start or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue

        try:
            sample = json.loads(line.strip("\n"))
        except Exception:
            continue

        if sample["status"] == enumeration.SAMPLE_STATUS_RTBI:
            count += 1
            measurement_target_list = [sample["ip"], ]
            guard_candidate_list = []
            for can in sample["candidates_merged"]:
                measurement_target_list.append(can["guard"]["guard"]["ip"])
                guard_candidate_list.append({"guard_ip": can["guard"]["guard"]["ip"], "candidate_coordinate": {"longitude": can["longitude"], "latitude": can["latitude"]}})

            coarse_grained_location = sample["result_fr_commercial_tool"]
            sorted(probe_list, key=lambda x: geo_distance_calculator.get_geodistance_btw_2coordinates(x["longitude"], x["latitude"], coarse_grained_location["longitude"], coarse_grained_location["latitude"]))
            fin_probe_list = probe_list[:100]
            random.shuffle(fin_probe_list)
            fin_probe_list = fin_probe_list[:25]
            fin_probe_list = [str(pb["id"]) for pb in fin_probe_list]
            tag = "inference-" + sample["ip"]

            task_list.append({"target_ip": sample["ip"], "guard_n_candidate_list": guard_candidate_list, "probe_list": fin_probe_list, "tag": tag})
        ind += 1
    return task_list


def measure(num_candidates, task_list, start_ind):
    batch_num = 100 // (num_candidates + 1)
    max_num_per_account = 5000 // (num_candidates + 1)
    for ind, task in enumerate(task_list[start_ind:]):
        measurement_target_list = [guard["guard_ip"] for guard in task["guard_n_candidate_list"]]
        measurement_target_list.append(task["target_ip"])

        account_ind = (ind + 1) // max_num_per_account
        if (account_ind + 1) > len(settings.RIPE_ACCOUNT_KEY):
            logger.war("hit the daily quota limitation ..., stop at ind: %d" % (start_ind + ind))
        account = settings.RIPE_ACCOUNT_KEY[account_ind]
        ripe = network_measurer.RipeAtlas(account["account"], account["key"])

        zone = pytz.country_timezones('us')[0]
        tz = pytz.timezone(zone)
        start_time = datetime.datetime.now(tz).timestamp() + 120 + ((ind + 1) // batch_num) * 900

        res = ripe.measure_by_ripe_oneoff_ping(measurement_target_list, task["probe_list"], start_time, [task["tag"],],
                                               "for inference")
        print(res)
        print(res.text)
    pass


if __name__ == "__main__":

    pass
