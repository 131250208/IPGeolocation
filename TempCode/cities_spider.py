import json
from Doraemon.OnlineSearch import google_KG
from Doraemon.Requests import proxies_dora
import time
import random


def crawl_google_kg(get_proxies_fun):
    org_name_dict = json.load(open("Sources/query_record/query_seed_dict_google_cloud_city.json", "r", encoding="utf-8"))
    org_list = []
    query_list = [org_name for org_name in org_name_dict.keys() if org_name_dict[org_name] == 0]
    for ind, org_name in enumerate(query_list):
        res = google_KG.get_entity(org_name, get_proxies_fun)
        if res is None:
            org_name_dict[org_name] = 1
            continue
        del res["is_org"]
        org_list.append(res)
        print(res)
        org_name_dict[org_name] = 1
        if ind % 10 == 0 or (ind + 1) == len(query_list):
            org_list_existing = json.load(open("Sources/yield/entity_list_google_cloud_city.json", "r", encoding="utf-8"))
            org_list_existing.extend(org_list)
            json.dump(org_list_existing, open("Sources/yield/entity_list_google_cloud_city.json", "w", encoding='utf-8'))
            json.dump(org_name_dict, open("Sources/query_record/query_seed_dict_google_cloud_city.json", "w", encoding='utf-8'))
            org_list.clear()

        random.seed(time.time())
        time.sleep(1 + 3 * random.random())


if __name__ == "__main__":
    pool = [
        "168.235.109.30:15623",
        "168.235.109.30:15622",
        "168.235.109.30:15621",
        "168.235.109.30:15620",
        "168.235.109.30:15619",
        "168.235.109.30:15618",
        "168.235.109.30:15617",
        "168.235.109.30:15616",
        "168.235.109.30:15615",
        "168.235.109.30:15614",
    ]
    proxies_dora.set_pool(pool)
    crawl_google_kg(proxies_dora.get_proxies_fr_pool)


