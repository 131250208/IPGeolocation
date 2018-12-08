from Tools import other_tools, web_mapping_services
import json
from LandmarksCollector import data_preprocessor as dp_lmc
from multiprocessing import Pool


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
    loc_list = json.load(open(loc_list_path, "r"))
    len_loc_list = len(loc_list)
    try:
        org_name_dict = json.load(open(org_name_dict_path, "r"))
    except Exception:
        org_name_dict = {}

    query_list = ["company", "Internet Technology", "isp", "institute", "organization", "school",
                  "university", "academic", "government", "technology", "corporate"]

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
                json.dump(loc_list, open(loc_list_path, "w"))
                json.dump(org_name_dict, open(org_name_dict_path, "w"))
    except Exception:
        json.dump(loc_list, open(loc_list_path, "w"))
        json.dump(org_name_dict, open(org_name_dict_path, "w"))


if __name__ == "__main__":
    '''
    generate locations for searching POI(points of interest)
    us: -125.75583, -66.01197, 25.80139, 49.05694
    '''
    #generate_locs_4_searching_poi(-125.75583, -66.01197, 25.80139, 49.05694, 0.05)


    '''
    search candidate geo coordinate by google map
    '''
    # args = [("H:\\Projects/data_preprocessed/samples_us_with_candidates_4.%d.json" % (i + 1), i + 1) for i in range(9)]
    # res = multiprocess(count, args, 9)
    # print(res)

    # size_list = [30783, 16983, 18306, 18254, 15510, 18438, 18386, 18266, 14586]
    # ind_list = [8327, 8316, 5140, 8319, 8314, 8327, 8338, 8296, 129]
    # args = [("H:\\Projects/data_preprocessed/samples_us_with_candidates_3.%d.json" % (i + 1), "H:\\Projects/data_preprocessed/samples_us_with_candidates_4.%d.json" % (i + 1), ind_list[i], i, 50000)
    #         for i in range(9) if ind_list[i] < size_list[i]]
    # multiprocess(dp_lmc.incorporate_candidates_fr_web_mapping_services, args, 9)

    '''
    crawl organization names from google nearby searching api
    '''
    # extract_org_names_batch("../Sources/loc/loc_0.json", "../Sources/org_names/org_names_0_test.json", 1000)
    # args = [("../Sources/loc/loc_%d.json" % i, "../Sources/org_names/org_names_full_%d.json" % i, 2800, i) for i in range(8)]
    # multiprocess(extract_org_names_batch, args, 8)

# ----------------------------------------------------------------------------------------------------------
    # # get coordinate from several commercial dbs
    # incorporate_coordinate_fr_commercial_db("H:\\Projects/data_preprocessed/http_80_us_0.5.json",
    #                                 "H:\\Projects/data_preprocessed/http_80_us_0.6.json", 0)

    # # filter pages with copyright
    # find_pages_with_copyright("H:\\Projects/data_preprocessed/http_80_us_0.6.json",
    #                           "H:\\Projects/data_preprocessed/pages_us_with_copyright_0.3.json",
    #                           417000) #

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

