import re
import json
from Tools import purifier, other_tools, ner_tool
from LandmarksCollector import owner_name_extractor

state_names_abbr = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
                 "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND",
                 "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
                        ]

state_names = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
                 "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
                 "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
                 "Montana", "Nebraska", "Nevada", "New hampshire", "New jersey", "New mexico", "New York",
                 "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode island",
                 "South carolina", "South dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
                 "West Virginia", "Wisconsin", "Wyoming",
                   ]


def exist_addr_info(html):
    key_words = ["address",
                 ]
    key_words += state_names

    for k in key_words:
        if k in html:
            return True

    return False


def exist_zipcode(html):
    patterns = ["%s \d{5}" % abbr for abbr in state_names_abbr]
    search = re.search("(%s)" % "|".join(patterns), html)
    if search:
        return True
    return False


org_name_dict = json.load(open("../Sources/org_names/org_name_dict_index/org_name_dict_index_0.json", "r"))


def exist_owner_name(owner_info_str):
    res = ner_tool.extract_org_name_fr_str(owner_info_str, org_name_dict)
    if len(res) > 0:
        return True
    return False


if __name__ == "__main__":
    in_file_path = "H:\\Projects/data_preprocessed/http_80_us_0.6.json"
    f_inp = open(in_file_path, "r", encoding="utf-8")

    ind = 0
    index_start = 0
    count_addr = 0
    count_zipcode = 0
    count_owner_info = 0
    for line in f_inp:
        if ind < index_start or line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % ind)
            ind += 1
            continue

        try:
            sample = json.loads(line.strip("\n"))
        except Exception:
            continue
        # if exist_addr_info(sample["html"]):
        #     count_addr += 1
        # if exist_zipcode(sample["html"]):
        #     count_zipcode += 1
        # print("------------addr: %d/%d-----zip: %d/%d-------" % (count_addr, ind + 1, count_zipcode, ind + 1))
        owner_info_str = owner_name_extractor.extract_owner_info_str(sample["html"])
        if exist_owner_name(owner_info_str):
            count_owner_info += 1
            # print("info_str: %s, \nowner_name: %s" % (owner_info_str, owner_name))

        print("------------owner_info: %d/%d---------------" % (count_owner_info, ind + 1))
        ind += 1
