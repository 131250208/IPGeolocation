from Tools import mylogger
from bs4 import BeautifulSoup
import json
import re
from LandmarksCollector import settings, owner_name_extractor, iterative_inference_machine
from Tools import commercial_db, purifier
logger = mylogger.Logger("../Log/data_preprocessor.py.log")
import time

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
        page_info = get_brief_one(line) if is_valid(line) else None
        if page_info is not None and check_title(page_info["title"]):
            location_info = commercial_db.get_location_info_by_commercial_tools(page_info["ip"])
            if location_info and location_info["country"] == "United States":
                # print("idc: %s, isp: %s, region: %s, city: %s, lon: %s, lat: %s" % (ipip["idc"], ipip["isp"], ipip["region"], ipip["city"], ipip["longitude"], ipip["latitude"]) )
                # print(page_info)

                out.write("%s\n" % json.dumps(page_info))
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


def filter_out_duplicates(input_file_path, out_file_path):
    inp_file = open(input_file_path, "r", encoding="utf-8")
    out_file = open(out_file_path, "a", encoding="utf-8")
    set_ip = set()
    count_duplicates = 0
    for ind, line in enumerate(inp_file):
        print("-----------------%d--------------------" % ind)
        page_info = json.loads(line)
        if page_info["ip"] not in set_ip:
            out_file.write("%s\n" % json.dumps(page_info))
            set_ip.add(page_info["ip"])
        else:
            logger.info("ip: %s is a duplicate...., del" % page_info["ip"])
            count_duplicates += 1
    out_file.close()
    print("count_duplicates: %d" % count_duplicates)


def find_pages_with_copyright(in_file_path, out_file_path, index):
    '''
    identify monitoring pages
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
            pageInfo = json.loads(line)
        except Exception:
            continue

        html = pageInfo["html"]
        soup = purifier.get_pure_soup_fr_html(html)

        org_fr_copyright = owner_name_extractor.extract_org_fr_copyright(soup)

        if len(org_fr_copyright) > 0:
            f_out.write("%s\n" % json.dumps(pageInfo))
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
            page_info = json.loads(line)
        except Exception:
            continue

        print("-----------------ind: %d, count of ambiguous ip: %d--------------------" % (ind, count_ambiguity))

        ip = page_info["ip"]
        ipinfo_fr_commercial_tools = commercial_db.get_location_info_by_commercial_tools(ip) # filter

        if ipinfo_fr_commercial_tools is None:
            count_ambiguity += 1
            ind += 1
            print("%s the city is ambiguous..." % ip)
            continue

        page_info["result_fr_commercial_tool"] = ipinfo_fr_commercial_tools
        f_out.write("%s\n" % json.dumps(page_info))

        ind += 1

    print("count_ambiguity: %d" % count_ambiguity)
    f_out.close()


# from gevent import monkey
# monkey.patch_socket()
# import gevent
#
#
# def search_candidates_by_gevent(list_jobs):
#     t1 = time.time()
#     gevent.joinall(list_jobs)
#     list_page_info = [job.value for job in list_jobs]
#     t2 = time.time()
#     print(t2 - t1)
#     return list_page_info


def incorporate_candidates_fr_web_mapping_services(in_file_path, out_file_path, index_start, index_end, tag=None):
    f_inp = open(in_file_path, "r", encoding="utf-8")
    f_out = open(out_file_path, "a", encoding="utf-8")

    ind = 0

    for line in f_inp:
        print("-----------tag: %s------ind: %d------end: %d----------------" % (tag, ind, index_end))
        if ind < index_start or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue
        elif ind >= index_end:
            break
        try:
            page_info = json.loads(line)
        except Exception:
            continue

        t1 = time.time()
        page_info = iterative_inference_machine.search_candidates(page_info,
                                                                  page_info["result_fr_commercial_tool"]["longitude"],
                                                                  page_info["result_fr_commercial_tool"]["latitude"],
                                                                  20000)
        t2 = time.time()

        print(t2 - t1)
        f_out.write("%s\n" % json.dumps(page_info))
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
            page_info = json.loads(line.strip("\n"))
        except Exception:
            continue

        candidates = page_info["result_fr_page"]["candidates"] + page_info["result_fr_registration_db"]["candidates"]
        candidates = iterative_inference_machine.merge_near_candidates(candidates, 2000)
        page_info["candidates_merged"] = candidates
        f_out.write("%s\n" % json.dumps(page_info))
        ind += 1

    f_out.close()


def get_initial_landmarks(inp_path, out_path):
    file = open(inp_path, "r")
    list_page_info = []
    count_landmarks = 0

    dict_landmarks_total = {}
    for line in file:
        list_page_info.append(json.loads(line))
        if len(list_page_info) == 10000:
            dict_landmarks = iterative_inference_machine.generate_landmarks(list_page_info)
            # print(json.dumps(dict_landmarks, indent=2))
            len_lm = len(list(dict_landmarks.keys()))
            dict_landmarks_total = {**dict_landmarks, **dict_landmarks_total}
            print(len_lm)
            count_landmarks += len_lm
            list_page_info.clear()

    dict_landmarks = iterative_inference_machine.generate_landmarks(list_page_info)
    len_lm = len(list(dict_landmarks.keys()))
    print(len_lm)
    print(len(dict_landmarks_total))
    json.dump(dict_landmarks_total, open(out_path, "w"))

    print("total: %d" % count_landmarks)


if __name__ == "__main__":


    # # get coordinate from several commercial dbs
    # incorporate_coordinate_fr_commercial_db("H:\\Projects/data_preprocessed/http_80_us_0.5.json",
    #                                 "H:\\Projects/data_preprocessed/http_80_us_0.6.json", 0)

    # # filter pages with copyright
    # find_pages_with_copyright("H:\\Projects/data_preprocessed/http_80_us_0.6.json",
    #                           "H:\\Projects/data_preprocessed/pages_us_with_copyright_0.3.json",
    #                           417000) #

    # # filter duplicate
    # filter_out_duplicates("H:\\Projects/data_preprocessed/http_80_us_0.2.json", "H:\\Projects/data_preprocessed/http_80_us_0.5.json")
    #
    #
    # # find samples in us
    # find_pages_us("H:\\Projects/HTTP数据/全球_HTTP_80/HTTP_80_deviceScanTask_1538017385_80_zgrab.json",
    #               "H:\\Projects/data_preprocessed/http_80_us_0.2.json", 51164702)# 3305K - 65K = 3240k saved

    # # search candidates
    # incorporate_candidates_fr_web_mapping_services("H:\\Projects/data_preprocessed/pages_us_with_copyright_0.2.json",
    #                                           "H:\\Projects/data_preprocessed/pages_us_with_candidates_0.1.json", 43326, 53212)

    # get initial landmarks
    # for i in range(8):
    #     num = i + 2
    #     inp_path = "H:\\Projects/data_preprocessed/pages_us_with_candidates_0.%d.json" % num
    #     out_path = "../Sources/landmarks_fr_cyberspace_0.%d.json" % num
    #     get_initial_landmarks(inp_path, out_path)

    # multiprocessing missions
    from multiprocessing import Pool

    p = Pool(9)
    start_indices = [0 for _ in range(9)]
    for i in range(9):
        p.apply_async(merge_near_candidates, args=("H:\\Projects/data_preprocessed/pages_us_with_candidates_0.%d.json" % (i + 1),
                                                  "H:\\Projects/data_preprocessed/samples_us_with_candidates_1.%d.json" % (i + 1),
                                                                       start_indices[i], i))

    p.close()
    p.join()

    # tag = [3]
    # p = Pool(8)
    # ind = 310
    # rec = [32000, 32000, 32000, 26836, 32000, 32000, 32000, 25515]
    # for i in tag:
    #     start = ind + i * 32000 + rec[i]
    #     end = ind + (i + 1) * 32000
    #     if start == end:
    #         print("start: %d, end: %d, the start is the same as the end, canceled" % (start, end))
    #         continue
    #     print("start: %d, end: %d" % (start, end))
    #     p.apply_async(search_candidates_by_web_mapping_services, args=("H:\\Projects/data_preprocessed/pages_us_with_copyright_0.3.json",
    #                                               "H:\\Projects/data_preprocessed/pages_us_with_candidates_0.%d.json" % (i + 2),
    #                                                                    start, end, i,))
    # p.close()
    # p.join()

    # tag = [3]
    # for i in tag:
    #     file = open("H:\\Projects/data_preprocessed/pages_us_with_candidates_0.%d.json" % (i + 2), "r")
    #     list_p = [line for line in file]
    #     print(len(list_p))

    pass
