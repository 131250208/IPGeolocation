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


def is_valid(line):
    '''
    check:
        not "\n",
        can be loaded by json,
        not error page,
        has status_code and it is 200

    :param line: a line of bytes read from file
    :return: boolen
    '''

    line = line.decode("utf-8")

    if line.strip("\n") == "":
        return False

    # filter json loading fail
    try:
        banner_info = json.loads(line)
    except Exception as e:
        logger.war(e)
        logger.war("error str can not be loads as json: %s" % line)
        return False

    if "error" in banner_info:  # filter error pages
        return False

    # filter samples without status code
    try:
        status_code = banner_info["data"]["http"]["response"]["status_code"]
    except Exception as e:
        logger.war(e)
        logger.war("has no status_code: %s" % line)
        return False

    if status_code != 200:  # filter pages of which status code is not 200
        return False
    return True


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


# --------------------------------batch processing---------------------------------------------------------------------


def find_pages_us(infilepath, outfilepath, index):
    '''
    for data from ipv4 space ~ 700G
    :param infilepath:
    :return:
    '''
    f = open(infilepath, "rb")
    out = open(outfilepath, "a", encoding="utf-8")

    ind = 0
    count_temp = 0
    save_size = 1000
    saved_time = 0
    for line in f:
        # print("----------------------%d--------------------" % ind)
        if ind < index:
            ind += 1
            continue
        sample = get_brief_one(line) if is_valid(line) else None
        if sample is not None and check_title(sample["title"]):
            location_info = geoloc_commercial_db.get_location_info_by_commercial_tools_unanimous(sample["ip"])
            if location_info and location_info["country"] == "United States":
                # print("idc: %s, isp: %s, region: %s, city: %s, lon: %s, lat: %s" % (ipip["idc"], ipip["isp"], ipip["region"], ipip["city"], ipip["longitude"], ipip["latitude"]) )
                # print(sample)

                out.write("%s\n" % json.dumps(sample))
                count_temp += 1
                if count_temp == save_size:
                    saved_time += 1
                    count_temp = 0
                    out.close()
                    out = open(outfilepath, "a", encoding="utf-8")
                    logger.war("--ind: %d---saved_time: %d---\n" % (ind, saved_time))
                # print("--ind: %d---saved_time: %d---\n"  % (ind, saved_time))
        ind += 1

    out.close()


def filter_out_invalid(input_file_path, out_file_path):
    '''
    invalid: duplicates and dead ones(can not ping)
    :param input_file_path:
    :param out_file_path:
    :return:
    '''
    inp_file = open(input_file_path, "r", encoding="utf-8")
    out_file = open(out_file_path, "a", encoding="utf-8")
    set_ip = set()
    count_duplicates = 0
    for ind, line in enumerate(inp_file):
        print("-----------------%d--------------------" % ind)
        sample = json.loads(line)
        if sample["ip"] not in set_ip and network_measurer.ping(sample["ip"], 1):
            out_file.write("%s\n" % json.dumps(sample))
            set_ip.add(sample["ip"])
        else:
            logger.info("ip: %s is a invalid...., del" % sample["ip"])
            count_duplicates += 1
    out_file.close()
    print("count_duplicates: %d" % count_duplicates)


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


def incorporate_coarse_locations_fr_commercial_dbs(*args):
    samples = args[0]
    for sample in samples:
        ip = sample["ip"]
        ipinfo_fr_commercial_tools = geoloc_commercial_db.get_locations_info_by_commercial_tools(ip)
        sample["result_fr_commercial_tool"] = ipinfo_fr_commercial_tools
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


def incorporate_candidates_fr_web_mapping_services(*args):
    samples = args[0]
    radius = args[1]

    new_samples = []
    for sample in samples:
        t1 = time.time()
        sample = iterative_inference_machine.search_candidates(sample, radius)
        new_samples.append(sample)
        t2 = time.time()
        print(t2 - t1)
    return new_samples


def merge_near_candidates(in_file_path, out_file_path, index_start, tag):
    f_inp = open(in_file_path, "r", encoding="utf-8")
    f_out = open(out_file_path, "a", encoding="utf-8")

    ind = 0
    for line in f_inp:
        print("-----------tag: %s------ind: %d------------" % (tag, ind, ))
        if ind < index_start or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue

        try:
            sample = json.loads(line.strip("\n"))
        except Exception:
            continue

        candidates = sample["result_fr_page"]["candidates"] + sample["result_fr_registration_db"]["candidates"]
        candidates = iterative_inference_machine.merge_near_candidates(candidates, 2000)
        sample["candidates_merged"] = candidates

        if len(candidates) == 1:
            sample["status"] = enumeration.SAMPLE_STATUS_FIN
            sample["coordinate"] = candidates[0]
        elif len(candidates) > 1:
            sample["status"] = enumeration.SAMPLE_STATUS_WFVG
        else:
            sample["status"] = enumeration.SAMPLE_STATUS_FAI

        f_out.write("%s\n" % json.dumps(sample))
        ind += 1

    f_out.close()


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
