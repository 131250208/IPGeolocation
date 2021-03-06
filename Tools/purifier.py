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


def get_pure_soup_fr_html(html, ignore_n=False):
    '''
    soup that without script, style and redundant blanks
    :param html:
    :param ignore_n: to remove all blanks or not
    :return: soup
    '''
    html = re.sub("<!-+.*?-+>", "", html)
    if ignore_n:
        html = re.sub("[\n\r]+", " ", html)
        html = re.sub("[\t\s ]+", " ", html)

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
    return soup


def prettify_text(text):
    return re.sub("[\r\t\n\s ]+", " ", text)


def filter_out_redundant_c(str, list_redandant_char):
    if str is None:
        return None

    compile_redundant_str = "(%s)" % "|".join(list_redandant_char)
    str = re.sub(compile_redundant_str, "", str, flags=re.I)
    return str


if __name__ == "__main__":
    html = re.sub("<!-+.*-+>", "", "<!------->")
    print(html)

