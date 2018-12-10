from bs4 import BeautifulSoup
from LandmarksCollector.data_preprocessor import is_valid, get_brief_one
import re
import settings
import logging
import json

def exist_loginform(html):
    soup = BeautifulSoup(html, "lxml")
    form_list = soup.select("form")

    list_loginForm = []
    for form in form_list:
        list_input = form.select("input")
        for input in list_input:
            if "type" in input.attrs:
                type = input["type"]
                if type.lower() == "password":
                    list_loginForm.append(form)
                    return True
    return False


def exist_keyword(list_keyword, text):
    for key in list_keyword:
        if key in text:
            return True
    return False


def exist_keyword_ignore_case(list_keyword, text):
    for key in list_keyword:
        if key.lower() in text.lower():
            return True
    return False


def identification(in_file_path, out_file_path, index):
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
    for line in f_inp:
        if ind < index and line.strip() == "\n":
            print("-----------------ind: %d pass--------------------" % (ind))
            ind += 1
            continue
        try:
            pageInfo = json.loads(line)
        except Exception:
            continue

        html = pageInfo["html"]
        if exist_loginform(html) and \
                (exist_keyword_ignore_case(settings.KEYWORD_MAN_SYS, pageInfo["title"]) or
                     exist_keyword(settings.KEYWORD_MAN_SYS_UP, pageInfo["title"])) and \
                not exist_keyword_ignore_case(settings.BlACK_LIST_INVALID_PAGE, pageInfo["title"]) and \
                not exist_keyword_ignore_case(settings.BlACK_LIST_DEVICE_CONF_MAN, pageInfo["title"]):

            f_out.write("%s\n" % json.dumps(pageInfo))
            logging.warning("-----------------ind: %d identification: %s--------------------" % (ind, True))
        else:
            print("-----------------ind: %d identification: %s--------------------" % (ind, False))
        ind += 1

    f_out.close()

if __name__ == "__main__":
    identification("D:\\data_preprocessed/http_80_us.json", "D:\\data_preprocessed/management_sys_us.json", 0)
    # f = open("D:\\data_preprocessed/management_sys_us.json", "r", encoding="utf-8")
    # count = 0
    # for line in f:
    #     if line.strip() != "\n":
    #         count += 1
    # print(count)