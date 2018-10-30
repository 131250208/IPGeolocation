import base64
from urllib import parse
import requests
import json
from Tools import settings, requests_tools as rt
from Tools import mylogger
logger = mylogger.Logger("../Log/ocr_tool.py.log")


def img_orc_google(img_url):
    api = "https://vision.googleapis.com/v1/images:annotate?key=%s" % settings.GOOGLE_API_KEY
    data = {
        "requests": [
            {
                "image": {
                    "source": {
                        "imageUri": img_url,
                    }
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION"
                    }
                ]
            }
        ]
    }
    if "http" not in img_url: # local path
        img = open(img_url, "rb")
        img_bs64 = base64.b64encode(img.read()).decode()
        data["requests"][0]["image"] = {"content": img_bs64}

    res = rt.try_best_request_post(api, json.dumps(data), 5, "img_orc_google", "abroad")
    if res.status_code == 200:
        json_res = json.loads(res.text)["responses"][0]
        if "error" in json_res:
            logger.war("%s: %s" % (img_url, json_res["error"]["message"]))
            return None
        else:
            try:
                text = json_res["textAnnotations"][0]["description"]
                logger.info("google ocr success!")
                return text
            except Exception:
                return None
    logger.war("bad response, status_code: %d" % res.status_code)
    return None


def img_orc_baidu(filePath):
    '''
    Baidu OCR API
    BAIDU_API_OCR_ACCURATE 500/d
    BAIDU_API_OCR_GENERAL 50000/d  it is bad
    :param filePath:
    :return: text in the image
    '''
    img = open(filePath, "rb")
    url = "%s?access_token=%s" % (settings.BAIDU_API_OCR_ACCURATE, settings.BAIDU_API_KEY)
    img_bs64 = base64.b64encode(img.read()).decode()
    data = {
        "language_type": "ENG",
        "detect_direction": "true",
        "probability": "true",
        "image": img_bs64
    }
    data = parse.urlencode(data)
    res = requests.post(url, data=data)
    # print(res.text)
    return json.loads(res.text)


if __name__ == "__main__":
    text = img_orc_google("https://www.wocao.com/jpg.png")
    print(text)