from LandmarksCollector import owner_name_extractor as oi
import json
from LandmarksCollector import settings, iterative_inference_machine



def test_org_extracter():
    landmarks = json.load(open("../Sources/landmarks_planetlab_0.3.json", "r"))
    for lm in landmarks:
        if lm["organization"] == "Palo Alto Research Center": # Palo Alto Research Center(1.8W)
            print(lm["geo_lnglat"]["pinpointed_area"])
            it = oi.get_org_info_fr_pageinfo(lm["html"], lm["url"])
            while True:
                try:
                    print(next(it))
                except StopIteration:
                    break
            print(lm["url"])


def test_copyright():
    pass
    # landmarks = json.load(open("../Sources/landmarks_planetlab_0.3.json", "r"))
    # for lm in landmarks:
    #     if lm["organization"] in settings.INVALID_LANDMARKS:
    #         continue
    #     if settings.INVALID_LANDMARKS_KEYWORD[0] in lm["organization"] or \
    #                     settings.INVALID_LANDMARKS_KEYWORD[1] in lm["organization"]:
    #         continue
    #         # ------------------------------------------------------
    #     if "geo_lnglat" not in lm:
    #         continue
    #     country = lm["geo_lnglat"]["country"]
    #     if country == "United States" and "ip" in lm and "html" in lm:
    #         soup = purifier.get_pure_soup_fr_html(lm["html"])
    #         list_copyright_info = oi.extract_copyright_info(soup)
    #         list_org_fr_copyright = oi.extract_org_fr_copyright(list_copyright_info)
    #         print("list_cpyinfo_raw: %s, list_cpy: %s" % (list_copyright_info, list_org_fr_copyright))


if __name__ == "__main__":
    ip2coord_total = {}
    list_name2val_total = []
    for i in range(9):
        file = open("../Sources/landmarks_fr_cyberspace_0.%d.json" % (i + 1), "r")
        ip2coord = json.load(file)

        ip2coord_total = {**ip2coord_total, **ip2coord}
    print(len(ip2coord_total))
    print(len(list_name2val_total))
    json.dump(ip2coord_total, open("../Sources/baidumap_inp_ip2co.json", "w"))
    json.dump(list_name2val_total, open("../Sources/baidumap_inp_name2val.json", "w"))

