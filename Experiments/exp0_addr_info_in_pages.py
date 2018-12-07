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


def exist_owner_name(html):
    soup = purifier.get_pure_soup_fr_html(html)
    title = owner_name_extractor.get_title(soup)
    logo_list = owner_name_extractor.extract_logo(soup)
    cpr = owner_name_extractor.extract_copyright_info(soup)

    logo_info_list = []
    for logo in logo_list:
        name = logo["src"].split("/")[-1].split(".")[0]
        word_list = other_tools.tokenize_v1(name)
        if "ubuntu" in word_list:
            pass
        words = [word for word in word_list if word not in other_tools.get_all_styles("logo")]
        name = " ".join(words)
        name_info = " ".join(other_tools.get_all_styles(name))

        logo_info_list.append("%s %s %s" % (logo["title"], logo["alt"], name_info))

    logo_info = " ".join(logo_info_list)

    owner_info = " ".join([title, logo_info, " ".join(cpr)])
    pattern = "|".join(other_tools.get_all_styles("logo"))
    owner_info = re.sub(pattern, "", owner_info)
    owner_info = re.sub("[\n\r\s\t]+", " ", owner_info)

    return ner_tool.org_name_extract(owner_info)


if __name__ == "__main__":
    in_file_path = "H:\\Projects/data_preprocessed/http_80_us_0.6.json"
    f_inp = open(in_file_path, "r", encoding="utf-8")

    ind = 0
    index_start = 0
    count_addr = 0
    count_zipcode = 0
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
        res = exist_owner_name(sample["html"])
        if len(res) > 0:
            print(res)
        ind += 1