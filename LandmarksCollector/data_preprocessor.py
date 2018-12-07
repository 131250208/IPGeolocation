from Tools import mylogger
from bs4 import BeautifulSoup
import json
import re
from LandmarksCollector import settings, owner_name_extractor, iterative_inference_machine, enumeration
from Tools import geoloc_commercial_db, purifier, geo_distance_calculator, network_measurer, settings as st_tool, web_mapping_services, ner_tool
import logging
logger = mylogger.Logger("../Log/data_preprocessor.py.log", clevel=logging.INFO)
import time
from multiprocessing import Pool
import random
import pytz
import datetime
import pyprind


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


def incorporate_coordinate_fr_commercial_db(in_file_path, out_file_path, index):
    '''
    filter out IPs of which the location is ambiguous, that is, whose results from commercial databases are very different
    '''

    f_inp = open(in_file_path, "r", encoding="utf-8")
    f_out = open(out_file_path, "a", encoding="utf-8")
    count_ambiguity = 0
    ind = 0
    for line in f_inp:
        if ind < index or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue
        try:
            sample = json.loads(line)
        except Exception:
            continue

        print("-----------------ind: %d, count of ambiguous ip: %d--------------------" % (ind, count_ambiguity))

        ip = sample["ip"]
        ipinfo_fr_commercial_tools = geoloc_commercial_db.get_location_info_by_commercial_tools_unanimous(ip) # filter

        if ipinfo_fr_commercial_tools is None:
            count_ambiguity += 1
            ind += 1
            print("%s the city is ambiguous..." % ip)
            continue

        sample["result_fr_commercial_tool"] = ipinfo_fr_commercial_tools
        f_out.write("%s\n" % json.dumps(sample))

        ind += 1

    print("count_ambiguity: %d" % count_ambiguity)
    f_out.close()


def incorporate_candidates_fr_web_mapping_services(in_file_path, out_file_path, start_ind, tag=None, radius=20000):
    f_inp = open(in_file_path, "r", encoding="utf-8")
    f_out = open(out_file_path, "a", encoding="utf-8")

    ind = 0

    for line in f_inp:
        print("-----------tag: %s------ind: %d-------------" % (tag, ind))
        if ind < start_ind or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue

        try:
            sample = json.loads(line)
        except Exception:
            continue

        t1 = time.time()
        sample = iterative_inference_machine.search_candidates(sample,
                                                                  sample["result_fr_commercial_tool"]["longitude"],
                                                                  sample["result_fr_commercial_tool"]["latitude"],
                                                                  radius)
        t2 = time.time()

        print(t2 - t1)
        f_out.write("%s\n" % json.dumps(sample))
        ind += 1
    f_out.close()


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
        if (account_ind + 1) > len(st_tool.RIPE_ACCOUNT_KEY):
            logger.war("hit the daily quota limitation ..., stop at ind: %d" % (start_ind + ind))
        account = st_tool.RIPE_ACCOUNT_KEY[account_ind]
        ripe = network_measurer.RipeAtlas(account["account"], account["key"])

        zone = pytz.country_timezones('us')[0]
        tz = pytz.timezone(zone)
        start_time = datetime.datetime.now(tz).timestamp() + 120 + ((ind + 1) // batch_num) * 900

        res = ripe.measure_by_ripe_oneoff_ping(measurement_target_list, task["probe_list"], start_time, [task["tag"],],
                                               "for inference")
        print(res)
        print(res.text)
    pass


def get_organization_name(in_file_path, index_start):
    f_inp = open(in_file_path, "r", encoding="utf-8")

    ind = 0
    org_set = set()
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

        res_page_info = sample["result_fr_page"]
        res_registration = sample["result_fr_registration_db"]
        # org_set.add(res_page_info["query"])
        # org_set.add(res_registration["query"])

        for can in res_page_info["candidates"]:
            org_set.add(can["org_name"])

        for can in res_registration["candidates"]:
            org_set.add(can["org_name"])
        ind += 1

    return list(org_set)


def multiprocess(job, args_list, num_pro):
    p = Pool(num_pro)

    res_list = []
    for i in range(len(args_list)):
        res = p.apply_async(job, args=args_list[i])
        res_list.append(res)
    p.close()
    p.join()

    return [res.get() for res in res_list]


def count(in_file_path, tag=None):
    f_inp = open(in_file_path, "r", encoding="utf-8")
    count = 0
    for _ in f_inp:
        count += 1
    return {"tag": tag, "count": count}


def extract_org_names_batch(loc_list_path, org_name_dict_path, tag=None):
    loc_list = json.load(open(loc_list_path, "r"))
    len_loc_list = len(loc_list)
    try:
        org_name_dict = json.load(open(org_name_dict_path, "r"))
    except Exception:
        org_name_dict = {}

    query_list = ["company", "Internet", "Website", "institution", "organization", "school", "university", "academic", "government"]

    try:
        for ind, loc in enumerate(loc_list):
            if loc["done"] == 1:
                continue

            for query in query_list:
                org_list = web_mapping_services.google_map_nearby_search(query, loc["longitude"], loc["latitude"],
                                                                         8000)
                for org in org_list:
                    org_name = org["org_name"]
                    org_name_dict[org_name] = 0
                    for ess in ner_tool.extract_essentials_fr_org_full_name(org_name):
                        org_name_dict[ess] = 0

            loc["done"] = 1
            print("-------tag: %s-----pro: %d/%d, num_org_names: %d----------" % (tag, ind + 1, len_loc_list, len(org_name_dict)))
            if (ind + 1) % 10 == 0:
                json.dump(loc_list, open(loc_list_path, "w"))
                json.dump(org_name_dict, open(org_name_dict_path, "w"))
    except Exception:
        json.dump(loc_list, open(loc_list_path, "w"))
        json.dump(org_name_dict, open(org_name_dict_path, "w"))


if __name__ == "__main__":
    # # get coordinate from several commercial dbs
    # incorporate_coordinate_fr_commercial_db("H:\\Projects/data_preprocessed/http_80_us_0.5.json",
    #                                 "H:\\Projects/data_preprocessed/http_80_us_0.6.json", 0)

    # # filter pages with copyright
    # find_pages_with_copyright("H:\\Projects/data_preprocessed/http_80_us_0.6.json",
    #                           "H:\\Projects/data_preprocessed/pages_us_with_copyright_0.3.json",
    #                           417000) #

    # extract_org_names_batch("../Sources/loc/loc_0.json", "../Sources/org_names/org_names_0_test.json",)
    args = [("../Sources/loc/loc_%d.json" % i, "../Sources/org_names/org_names_%d.json" % i, i) for i in range(8)]
    multiprocess(extract_org_names_batch, args, 8)

    # filter duplicate
    # filter_out_invalid("H:\\Projects/data_preprocessed/http_80_us_0.2.json", "H:\\Projects/data_preprocessed/http_80_us_0.5.json")
    #
    #
    # # find samples in us
    # find_pages_us("H:\\Projects/HTTP数据/全球_HTTP_80/HTTP_80_deviceScanTask_1538017385_80_zgrab.json",
    #               "H:\\Projects/data_preprocessed/http_80_us_0.2.json", 51164702)# 3305K - 65K = 3240k saved

    # # search candidates
    # incorporate_candidates_fr_web_mapping_services("H:\\Projects/data_preprocessed/samples_us_with_candidates_3.1.json",
    #                                           "H:\\Projects/data_preprocessed/samples_us_with_candidates_4.1.json", radius=50000)

    # args = [("H:\\Projects/data_preprocessed/samples_us_with_candidates_4.%d.json" % (i + 1), i + 1) for i in range(9)]
    # res = multiprocess(count, args, 9)
    # print(res)

    # size_list = [30783, 16983, 18306, 18254, 15510, 18438, 18386, 18266, 14586]
    # ind_list = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    # args = [("H:\\Projects/data_preprocessed/samples_us_with_candidates_3.%d.json" % (i + 1), "H:\\Projects/data_preprocessed/samples_us_with_candidates_4.%d.json" % (i + 1), ind_list[i], i, 50000) for i in range(9)]
    # multiprocess(incorporate_candidates_fr_web_mapping_services, args, 9)

    # # merge candidates
    # p = Pool(9)
    # start_indices = [0 for _ in range(9)]
    # for i in range(9):
    #     p.apply_async(merge_near_candidates, args=("H:\\Projects/data_preprocessed/pages_us_with_candidates_0.%d.json" % (i + 1),
    #                                               "H:\\Projects/data_preprocessed/samples_us_with_candidates_2.%d.json" % (i + 1),
    #                                                                    start_indices[i], i))
    #
    # p.close()
    # p.join()

    # # slice sample file by the number of candidates
    # start_indices = [0 for _ in range(9)]
    # for i in range(9):
    #     num = i + 1
    #     inp_path = "H:\\Projects/data_preprocessed/samples_us_with_candidates_2.%d.json" % num
    #     slice_sample_file_by_num_of_candidates(inp_path, "H:\\Projects/data_preprocessed/sample_us_with_x_candidates", start_indices[i])


    # # get initial landmarks
    # ip2coord_total = {}
    # for i in range(9):
    #     num = i + 1
    #     inp_path = "H:\\Projects/data_preprocessed/samples_us_with_candidates_2.%d.json" % num
    #     ip2coord = get_initial_landmarks(inp_path)
    #     ip2coord_total = {**ip2coord_total, **ip2coord}
    #
    # print(len(ip2coord_total))
    # json.dump(ip2coord_total, open("../Sources/landmarks_fr_cyberspace_1.json", "w"))

    # ip2coord = get_initial_landmarks("H:\\Projects/data_preprocessed/sample_us_with_x_candidates/sample_us_with_1_candidates.json")
    # print(len(ip2coord))
    # json.dump(ip2coord, open("../Sources/landmarks_fr_cyberspace_1.json", "w"))

    # # check landmarks by ping
    # dict_landmarks = json.load(open("../Sources/landmarks_fr_cyberspace_1.json", "r"))
    # dict_landmarks = check_landmarks(dict_landmarks)
    # json.dump(dict_landmarks, open("../Sources/landmarks_fr_cyberspace_2.json", "w"))

    # # match guards to their corresponding candidates
    # match_guards_to_candidates("H:\\Projects/data_preprocessed/sample_us_with_x_candidates/sample_us_with_2_candidates.json", "H:\\Projects/data_preprocessed/sample_us_with_x_candidates_guards_matched/sample_us_with_2_candidates_guards_matched.json", 0)

    # # measure the target and guards and infer
    # task_list = get_measurment_tasks_fot_inference("H:\\Projects/data_preprocessed/sample_us_with_x_candidates_guards_matched/sample_us_with_2_candidates_guards_matched.json", 0)
    # json.dump(task_list, open("../Sources/tasks/task_list_2_can.json", "w"))

    # task_list = json.load(open("../Sources/tasks/task_list_2_can.json", "r"))
    # measure(2, task_list, 0)
    pass
