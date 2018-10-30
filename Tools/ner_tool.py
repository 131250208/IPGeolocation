import ner
tagger = ner.SocketNER(host='localhost', port=8080)


def ner_stanford(copyright_info):
    result = tagger.get_entities(copyright_info)
    return result

if __name__ == "__main":
    res = ner_stanford("Palo Alto Research Center Incorporated; © 2018. All Rights Reserved")
    print(res)