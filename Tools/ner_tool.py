import ner
tagger = ner.SocketNER(host='localhost', port=8080)


def ner_stanford(copyright_info):
    result = tagger.get_entities(copyright_info)
    return result

if __name__ == "__main__":
    # res = ner_stanford("Palo Alto Research Center Incorporated; © 2018. All Rights Reserved")
    ner_res = ner_stanford("Incorporated in 2002, PARC (formerly Xerox PARC) has pioneered many technology ... 2002-2018 Palo Alto Research Center Incorporated; all rights reserved.")
    print(ner_res)