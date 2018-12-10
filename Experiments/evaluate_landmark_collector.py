import json
import settings
from Tools import geo_distance_calculator


def show_results_coordinating_on_planet_lab():
    landmarks = json.load(open("../Sources/landmarks_planetlab_0.3.json", "r"))

    count_us = 0
    count_fail = 0
    count_mul = 0
    error_dis = 0
    count = 0
    count_suc = 0
    invalid = []
    for lm in landmarks:
        #     # ------------------------------------------------------
        if "geo_lnglat" not in lm:
            continue
        country = lm["geo_lnglat"]["country"]
        if country == "United States" and "ip" in lm and "html" in lm:

            # if lm["organization"] in settings.INVALID_LANDMARKS:
            #     continue
            if settings.INVALID_LANDMARKS_KEYWORD[0] in lm["organization"] or \
                            settings.INVALID_LANDMARKS_KEYWORD[1] in lm["organization"]:
                # print(lm["organization"])
                # print(lm["url"])
                continue

            area_pinpointed = lm["geo_lnglat"]["pinpointed_area"]

            org = lm["organization"]
            coordi = geo_distance_calculator.google_map_coordinate(org + " " + area_pinpointed)
            if len(coordi) == 0:
                dis_ground = -1
            else:
                dis_ground = geo_distance_calculator.get_geodistance_btw_2coordinates(coordi[0]["lng"], coordi[0]["lat"], float(lm["longitude"]),
                                                                                      float(lm["latitude"]))
            logger.war("org: %s, res_num:%d, ground_truth_dis: %s" % (org, len(coordi), dis_ground))
            if dis_ground > 3000:
                count_fail += 1
                invalid.append(lm["organization"])
            else:
                count_suc += 1
    print("%s, %s" % (count_suc, count_fail))
    print(invalid)
         # -----------------------------------------------------------------------------------
    #         coordi = []
    #         last_query = ""
    #         it = get_org_info(lm["html"], lm["url"])
    #
    #         query = ""
    #         while True:
    #             try:
    #                 query = next(it)
    #             except StopIteration:
    #                 last_query = query
    #                 break
    #             coordi = geolocation.google_map_coordinate(query + " " + area_pinpointed)
    #             if len(coordi) > 0:
    #                 last_query = query
    #                 break
    #
    #         if len(coordi) == 0:
    #             count_fail += 1
    #             logger.war("--fail... org: %s, query: %s, area: %s" % (org, last_query, area_pinpointed))
    #
    #         elif len(coordi) > 0:
    #             dis_pre = geolocation.geodistance(coordi[0]["lng"], coordi[0]["lat"], float(lm["longitude"]),
    #                                               float(lm["latitude"]))
    #             logger.war("last_query: %s, res_num: %d, pre_dis: %s" % (last_query, len(coordi), dis_pre))
    #             error_dis += dis_pre
    #             if len(coordi) > 1:
    #                 count_mul += 1
    #         count_us += 1
    # logger.war("suc: %d, fail: %d, mul: %d, mean_error_dis: %s" % (count_us - count_fail, count_fail, count_mul, error_dis / (count_us - count_fail)))

