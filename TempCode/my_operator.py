from Tools import other_tools, web_mapping_services, ner_tool, geo_distance_calculator, mylogger
import json
from LandmarksCollector import data_preprocessor as dp_lmc, iterative_inference_machine as iim, owner_name_extractor as one
from multiprocessing import Pool
import settings
import numpy as np
import logging
logger = mylogger.Logger("../Log/my_operator.log", logging.DEBUG, logging.INFO)
import strings
import enumeration
import os

def frange(x, y, jump):
    '''
    range() for float
    :param x:
    :param y:
    :param jump:
    :return:
    '''
    while x < y:
        yield x
        x += jump
    yield y


def generate_locs_4_searching_poi(lon_lower, lon_upper, lat_lower, lat_upper, stride):
    '''
    generate locations for searching POI(points of interest)
    us: -125.75583, -66.01197, 25.80139, 49.05694
    :param lon_lower:
    :param lon_upper:
    :param lat_lower:
    :param lat_upper:
    :param stride:
    :return:
    '''
    list_lon = list(frange(lon_lower, lon_upper, stride))
    list_lat = list(frange(lat_lower, lat_upper, stride))
    coordinates = [{"longitude": lon, "latitude": lat, "done": 0} for lon in list_lon for lat in list_lat]

    list_lon = list(frange(lon_lower - stride/2, lon_upper + stride/2, stride))
    list_lat = list(frange(lat_lower - stride/2, lat_upper + stride/2, stride))
    coordinates_2 = [{"longitude": lon, "latitude": lat, "done": 0} for lon in list_lon for lat in list_lat]
    coordinates += coordinates_2
    print(len(coordinates))

    chunks = other_tools.chunks_avg(coordinates, 8)
    for ind, chunk in enumerate(chunks):
        json.dump(chunk, open("../Sources/loc/loc_%d.json" % ind, "w"))


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

        for can in res_page_info["candidates"]:
            org_set.add(can["org_name"])

        for can in res_registration["candidates"]:
            org_set.add(can["org_name"])
        ind += 1

    return list(org_set)


def extract_org_names_batch(loc_list_path, org_name_dict_path, radius, tag=None):
    loc_list = json.load(open(loc_list_path, "r", encoding="utf-8"))
    len_loc_list = len(loc_list)
    try:
        org_name_dict = json.load(open(org_name_dict_path, "r", encoding="utf-8"))
    except Exception:
        org_name_dict = {}

    query_list = ["company", "Internet Technology", "ISP", "institute", "organization", "school",
                  "university", "academic", "government", "technology", "corporation"]

    try:
        for ind, loc in enumerate(loc_list):
            if loc["done"] == 1:
                continue

            for query in query_list:
                org_list = web_mapping_services.google_map_nearby_search(query, loc["longitude"], loc["latitude"],
                                                                         radius)
                for org in org_list:
                    org_name = org["org_name"]
                    org_name_dict[org_name] = 0

            loc["done"] = 1
            print("-------tag: %s-----pro: %d/%d, num_org_names: %d----------" % (tag, ind + 1, len_loc_list, len(org_name_dict)))
            if (ind + 1) % 10 == 0:
                json.dump(loc_list, open(loc_list_path, "w", encoding="utf-8"))
                json.dump(org_name_dict, open(org_name_dict_path, "w", encoding="utf-8"))
    except Exception:
        json.dump(loc_list, open(loc_list_path, "w", encoding="utf-8"))
        json.dump(org_name_dict, open(org_name_dict_path, "w", encoding="utf-8"))


def process_large_file(in_file_path, out_file_path, index_start, function, *extra_args_4_func):
    '''
    process a huge number of samples in large file
    :param function: operation function
    :param extra_args_4_func: args for function except for 'samples'
    :param in_file_path: file with raw samples
    :param out_file_path: file to write new samples into
    :param index_start: start position
    :return: None
    '''

    f_inp = open(in_file_path, "r", encoding="utf-8")
    f_out = open(out_file_path, "a", encoding="utf-8")
    ind = 0
    out_size = 0
    batch = []
    for line in f_inp:
        if ind < index_start or line.strip() == "\n":
            print("----------pid: %s-------ind: %d pass--------------------" % (os.getpid(), ind))
            ind += 1
            continue
        try:
            sample = json.loads(line)
        except Exception:
            continue

        batch.append(sample)

        if len(batch) == 1000:
            samples_done = function(batch, *extra_args_4_func)
            for sample in samples_done:
                f_out.write("%s\n" % json.dumps(sample))
            out_size += len(samples_done)
            batch.clear()
            ind += 1000
            print("----------pid: %s-------%d/%d-------------------" % (os.getpid(), out_size, ind))

    if len(batch) != 0:
        samples_done = function(batch, *extra_args_4_func)
        for sample in samples_done:
            f_out.write("%s\n" % json.dumps(sample))
        batch.clear()
        out_size += len(samples_done)
        ind += len(batch)
        print("---------pid: %s--------%d/%d-------------------" % (os.getpid(), out_size, ind))


def slice_large_file(large_file_path, target_dir, chunk_size):
    f_inp = open(large_file_path, "r", encoding="utf-8")
    f_out = None
    ind = 0

    for line in f_inp:
        if line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue
        try:
            sample = json.loads(line)
        except Exception:
            continue

        if ind % chunk_size == 0:
            f_out = open("%s/slice_%d.json" % (target_dir, int(ind / chunk_size)), "a", encoding="utf-8")
        f_out.write("%s\n" % json.dumps(sample))
        ind += 1

        print("-----------------%d-------------------" % ind)


if __name__ == "__main__":
    # ---------------------------------------dict--------------------------------------------------------------------
    '''
    generate locations for searching POI(points of interest)
    us: -125.75583, -66.01197, 25.80139, 49.05694
    '''
    #generate_locs_4_searching_poi(-125.75583, -66.01197, 25.80139, 49.05694, 0.05)


    '''
    get org name from local files
    '''
    # args = [("H:\\Projects/data_preprocessed/pages_us_with_candidates_0.%d.json" % (i + 1), 0) for i in range(9)]
    # res_list = multiprocess(get_organization_name, args, 9)
    #
    # org_name_dict_index = {}
    # for res in res_list:
    #     for org_name in res:
    #         org_name_dict_index[org_name] = 0
    #
    # json.dump(org_name_dict_index, open("../Sources/org_names/org_names_full_8.json", "w"))


    '''
    crawl organization names from google nearby searching api
    '''
    # args = [("../Sources/loc/loc_%d.json" % i, "../Sources/org_names/org_names_full_%d.json" % i, 2800, i) for i in range(8)]
    # multiprocess(extract_org_names_batch, args, 8)

    '''
    build org name dict
    '''
    # path_list = ["../Sources/org_names/org_name_dict_{}.json".format(0)]
    # org_name_dict_index = ner_tool.build_indexes_4_org_name_dict(path_list)
    # json.dump(org_name_dict_index, open("../Sources/org_names/org_name_dict_index/org_name_dict_index_2.json", "w"))

# -----------------------------------------process samples--------------------------------------------------------------
    '''
    filter out IPs in the US
    '''
    # process_large_file("H:\\Projects/HTTP数据/全球_HTTP_80/HTTP_80_deviceScanTask_1538017385_80_zgrab.json",
    #                    "H:\\Projects/data_preprocessed/http_80_us_0.7.json", 0, dp_lmc.filter_ips_in_us,
    #                    )

    '''
    filter out duplicates and invalid(dead) ones
    '''
    # process_large_file("H:\\Projects/data_preprocessed/http_80_us_0.7.json", "H:\\Projects/data_preprocessed/http_80_us_0.8.json", 0, dp_lmc.filter_out_duplicates_n_invalid_samples, set())

    '''
    extract org names
    '''
    # org_name_dict = json.load(open("../Sources/org_names/org_name_dict_index/org_name_dict_index_0.json", "r"))
    # process_large_file("H:\\Projects/data_preprocessed/http_80_us_1.0.json",
    #                           "H:\\Projects/data_preprocessed/http_80_us_1.1.json",
    #                    0, dp_lmc.filter_samples_with_org_names, org_name_dict) #

    # samples = json.load(open("../Sources/experiments/samples_planetlab_us_0.1.json", "r", encoding="utf-8"))
    # samples = dp_lmc.extract_org_names(samples, org_name_dict)
    # json.dump(samples, open("../Sources/experiments/samples_planetlab_us_0.1.json", "w", encoding="utf-8"))

    '''
    get coordinate from several commercial dbs
    '''
    # process_large_file("H:\\Projects/data_preprocessed/http_80_us_0.9.json",
    #                    "H:\\Projects/data_preprocessed/http_80_us_1.0.json", 0, dp_lmc.incorporate_coarse_locations_fr_commercial_dbs, )

    # samples = json.load(open("../Sources/experiments/samples_planetlab_us_0.1.json", "r", encoding="utf-8"))
    # samples = dp_lmc.incorporate_coarse_locations_fr_commercial_dbs(samples)
    # json.dump(samples, open("../Sources/experiments/samples_planetlab_us_0.1.json", "w", encoding="utf-8"))

    '''
    slice large file
    '''
    # slice_large_file("H:\\Projects/data_preprocessed/http_80_us_1.1.json", "H:\\Projects/data_preprocessed/http_80_us_1.1_slices", 240000)

    '''
    search candidate geo coordinate by google map
    '''
    # samples = json.load(open("../Sources/experiments/samples_planetlab_us_0.1.json", "r", encoding="utf-8"))
    # samples = dp_lmc.incorporate_candidates_fr_web_mapping_services(samples, settings.RADIUS_FOR_SEARCHING_CANDIDATES)
    # json.dump(samples, open("../Sources/experiments/samples_planetlab_us_0.1.json", "w", encoding="utf-8"))

    # args = [("H:\\Projects/data_preprocessed/http_80_us_1.1_slices_with_candidates/slice_%d.json" % i, i) for i in range(8)]
    # res = multiprocess(count, args, 8)
    # print(res)

    # size_list = [240000, 240000, 240000, 240000, 240000, 240000, 240000, 193429]
    # ind_list = [12000, 16000, 13000, 15000, 13000, 13000, 5000, 13000]
    # args = [("H:\\Projects/data_preprocessed/http_80_us_1.1_slices/slice_%d.json" % i,
    #          "H:\\Projects/data_preprocessed/http_80_us_1.1_slices_with_candidates/slice_%d.json" % i,
    #          ind_list[i], dp_lmc.incorporate_candidates_fr_web_mapping_services, settings.RADIUS_FOR_SEARCHING_CANDIDATES)
    #         for i in range(8) if ind_list[i] < size_list[i]]
    # multiprocess(process_large_file, args, 8)


    '''
    merge near candidates
    '''
    # samples = json.load(open("../Sources/experiments/samples_planetlab_us_0.1.json", "r", encoding="utf-8"))
    # samples = dp_lmc.merge_near_candidates(samples)
    # json.dump(samples, open("../Sources/experiments/samples_planetlab_us_0.1.json", "w", encoding="utf-8"))

    '''
    get initial landmarks
    '''
    # samples = json.load(open("../Sources/experiments/samples_planetlab_us.json", "r", encoding="utf-8"))

    # planetlab_dict = json.load(open("../Sources/experiments/dataset_planetlab_us_dict.json", "r", encoding="utf-8"))
    # for ip, loc in planetlab_dict.items():
    #     query_fr_page = planetlab_dict[ip]["result_fr_page"]["query"]
    #     query_fr_registration_db = planetlab_dict[ip]["result_fr_registration_db"]["query"]
    #     if query_fr_page is None:
    #         ground_org = planetlab_dict[ip]["organization"]
    #         print("ground_org: %s, registry_org: %s" % (ground_org, query_fr_registration_db))
    #         print(one.extract_owner_info_str(loc["html"]))

    # ini_dict = iim.generate_initail_landmarks(samples)
    # print(ini_dict)
    # print(len(ini_dict))
    # error_list = []
    # for ip, loc in ini_dict.items():
    #     ground_lon = planetlab_dict[ip]["longitude"]
    #     ground_lat = planetlab_dict[ip]["latitude"]
    #     estimate_lon = ini_dict[ip]["longitude"]
    #     estimate_lat = ini_dict[ip]["latitude"]
    #     error_dis = geo_distance_calculator.get_geodistance_btw_2coordinates(ground_lon, ground_lat, estimate_lon, estimate_lat)
    #     # print(dis)
    #     if error_dis > 5000:
    #         # merged_loc = planetlab_dict[ip]["candidates_merged"]
    #         # print(json.dumps(merged_loc, indent=2))
    #         query_fr_page = planetlab_dict[ip]["result_fr_page"]["query"]
    #         query_fr_registration_db = planetlab_dict[ip]["result_fr_registration_db"]["query"]
    #         ground_org = planetlab_dict[ip]["organization"]
    #         res = planetlab_dict[ip]["candidates_merged"][0]
    #         logger.info("\n ip: %s, \nerror dis: %f, \nquery_p: %s, \nquery_r: %s, \nground_org: %s, \nres: %s" % (ip, error_dis, query_fr_page, query_fr_registration_db, ground_org, res))
    #     error_list.append(error_dis)
    #
    # print("median error distance: %f " % np.median(error_list))

    '''
    get observers and landmarks for inference
    '''
    # samples = json.load(open("../Sources/experiments/samples_planetlab_us.json", "r", encoding="utf-8"))

    # dp_lmc.incorporate_observers_n_landmarks(samples)
    # json.dump(samples, open("../Sources/experiments/samples_planetlab_us.json", "w", encoding="utf-8"))

# ----------------------------------------------------------------------------------------------------------


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

