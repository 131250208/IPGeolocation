from bs4 import BeautifulSoup
from LandmarksCollector.SampleReader import is_valid, get_brief_one
import re
from LandmarksCollector import settings

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
        if key in text.lower():
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

    ind = 0
    for sample in f_inp:
        if ind < index:
            print("-----------------ind: %d pass--------------------" % (ind))
            ind += 1
            continue

        if not is_valid(sample): continue

        pageInfo = get_brief_one(sample)
        html = pageInfo["html"]
        if exist_loginform(html) and exist_keyword(settings.KEYWORD_MONITOR, pageInfo["title"]):
            filename = re.sub("[\\x21-\\x2c\\x2e\\x2f\\x3a-\\x40\\\x5b-\\x60\\x7b-\\x7e]+", "_", pageInfo["title"])
            filename = re.sub("[\n\r\t]", "", filename)
            filename = filename.strip()

            try:
                f_out = open("%s/%s.html" % (out_file_path, filename), "w", encoding="utf-8")
            except Exception as e:
                continue
            f_out.write(pageInfo["html"])
            f_out.write('<a href="%s" class="host">%s</a>' % (pageInfo["host"], pageInfo["host"]))
            f_out.write('<a href="%s" class="path">%s</a>' % (pageInfo["url"], pageInfo["url"]))
            f_out.close()
            logging.warning("-----------------ind: %d identification: %s--------------------" % (ind, True))
        else:
            print("-----------------ind: %d identification: %s--------------------" % (ind, False))
        ind += 1