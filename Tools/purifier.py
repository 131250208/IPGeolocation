from bs4 import BeautifulSoup
import re

def get_pure_text_fr_html(html):
    '''
    get pure texts that people can see from browses
    :param html:
    :return: pure text
    '''

    soup = BeautifulSoup(html, "lxml")

    head = soup.select_one("head")
    if head is not None:
        head.decompose()

    scripts = soup.select("script")
    for sc in scripts:
        sc.decompose()

    style = soup.select("style")
    for st in style:
        st.decompose()

    text = soup.text
    text = re.sub("[\n\r]+", "\n", text)
    text = re.sub("[\t\s]+", " ", text)
    return text


def get_pure_body_fr_html(html):
    soup = BeautifulSoup(html, "lxml")

    # head = soup.select_one("head")
    # if head is not None:
    #     head.decompose()

    scripts = soup.select("script")
    for sc in scripts:
        sc.decompose()

    style = soup.select("style")
    for st in style:
        st.decompose()

    html = soup.prettify()
    html = re.sub("[\n\r]+", " ", html)
    html = re.sub("[\t\s ]+", " ", html)
    return html

def prettify_text(text):
    return re.sub("[\r\t\n\s ]+", " ", text)

