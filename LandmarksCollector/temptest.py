from LandmarksCollector import org_extracter as oi
from Tools import purifier
import json
from LandmarksCollector import settings


def test_org_extracter():
    landmarks = json.load(open("../resources/landmarks_planetlab_0.3.json", "r"))
    for lm in landmarks:
        if lm["organization"] == "Palo Alto Research Center": # Palo Alto Research Center(1.8W)
            print(lm["geo_lnglat"]["pinpointed_area"])
            it = oi.query_str(lm["html"], lm["url"])
            while True:
                try:
                    print(next(it))
                except StopIteration:
                    break
            print(lm["url"])


def test_copyright():
    pass
    # landmarks = json.load(open("../resources/landmarks_planetlab_0.3.json", "r"))
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
    from LandmarksCollector import landmarks
    landmarks.search_lm_from_web("../resources/universities_us_0.9.json")
