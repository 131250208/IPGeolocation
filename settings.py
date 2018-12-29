BlACK_LIST_INVALID_PAGE = ["IIS", "please wait", "404", "403", "not found", "coming soon", "please come back",
                           "wall", "error", "wireless", "gateway", "freebox",]
BlACK_LIST_DEVICE_CONF_MAN = ["router configuration", "camera", "remote management", "webcam"]

KEYWORD_MAN_SYS = ["human resource", "financial", "customer relationship",
                   "certification", "inventory", "stock", "product", "admin", "administra"] # , "surveillance", "monitoring", "監視", "モニタリング", "监控", "監控"
KEYWORD_MAN_SYS_UP = ["CTCA", "GFA", "IDSTAR", "CAS", "OA", "ERP", "CRM", "HRM", "ASCC",
                     "FMIS", "FMIS", "OSS", "RMS", "OMS","ECC", "PMS", "BPM"]


KEYWORD_CLOUD_PROVIDER = ["amazon.com", "cloudflare.com", "cloud.google.com", "liquidweb.com", "akamai.com",
                "fastly.com", # edge cloud provider
                "level3.com", # CDN
                "digitalocean.com",
                "godaddy.com",
                "singlehop.com",
                "layer3com.com",
                "google.com",
                "onenet.net", # Cloud Storage Solutions
                "ncren.net",
                "pch.net",
                ]

COMPANY_ABBR = ["Inc.", "LLC", "L.L.C", "Ltd.", "Co.", "company", "incorporated", "Corporation"] # "logo", "footer", "header", "body", "foot", "head", "brand", "smaller", "bigger", "text",
                                                                                            # "home", "login", "system", "official site", "welcome", "main",

BlACK_LIST_LOGO = ["button", "btn", "login", "submit"]

REDUNDANT_LIST_COPYRIGHT = ["Infringement", "Privacy Statement", "Privacy Policy", "Disclaimer", "Nondiscrimination",
                        "All Rights Reserved", "Copyright", "Supported by", "NSF", "Site Policies", "Site Contact"
                        "Phone", "Fax", "Site Contact"]

# invalid Planetlab landmarks
INVALID_PLANETLAB_NODES = ["University of California, Davis",
                            "Oregon State University School of Electrical Engineering and Computer Science",
                           "Iowa State University Electrical and Computer Engineering",
                           "San Jose State University",
                           "Packet Clearing House - San Francisco",
                           "University of Oklahoma",
                           "George Mason University",
                           "Georgetown University",
                           ]
# > 5000
# INVALID_LANDMARKS = ['HP Labs', 'University of Central Florida - EECS', 'Northeastern University CCIS', 'University of California, Riverside', 'University of California at Santa Barbara', 'HP Labs', 'Google', 'University of Rochester', 'University of California, Davis', 'University of Delaware', 'University of Southern California, ISI', 'Loyola University Chicago', 'University of Florida - ACIS Lab', 'San Jose State University']

# > 3000
# INVALID_LANDMARKS = ['HP Labs', 'University of Michigan', 'NEC Laboratories', 'University of Central Florida - EECS', 'Northeastern University CCIS', 'University of California, Riverside', 'University of California at Santa Barbara', 'HP Labs', 'Google', 'Rutgers University', 'University of Rochester', 'University of Connecticut', 'University of California, Davis', 'University of Wisconsin', 'New York Institute of Technology', 'University of Delaware', 'University of Southern California, ISI', 'University of Georgia', 'University of Nebraska - Lincoln', 'Loyola University Chicago', 'University of Florida - ACIS Lab', 'University of California, Irvine', 'San Jose State University', 'University of Washington - Accretive DSL', 'North Carolina State University']
INVALID_LANDMARKS_KEYWORD = ["MLab", "MeasurementLab",]
# 结点并没有部署在本地，机构地址和结点定位相距超过5KM， -1机构不在节点当前city, 查一查ISP是不是云服务商，查一查确切地址确认是搜索不成功还是真的不在本地

# 提供了多个ip结点，但只提供了一个站点（机构主页），无法确定在pl上的结点地址对应哪一个ip， 并且没有部署在本地(结点本地搜索不到该机构)
# MLab - DFW06、MLab - LGA0T， MLab - LGA0T， MLab - IAD0T，。。。  MeasurementLab

# 机构当地有多个定位
# University of California, Riverside

# 链接网页过期
# Oklahoma State University (Tulsa)


# 论文示例
# http://www.ittc.ku.edu/的logo


# -----------------------------------------------

# proxies
PROXY_LOC_SHADOW = "127.0.0.1:1080"
PROXY_LUMI_ACCOUNT = "lum-customer-hl_95db9f83-zone-zone1"
PROXY_LUMI_PASS = "1bgiacxdl2xa"
PROXY_DATA5U_SPIDER_API = "http://api.ip.data5u.com/dynamic/get.html?order=53b3de376027aa3f699dc335d2bc0674&sep=3"
PROXY_DATA5U_ABROAD_SPIDER_API = "http://api.ip.data5u.com/api/get.shtml?order=53b3de376027aa3f699dc335d2bc0674&num=100&area=%E7%BE%8E%E5%9B%BD&carrier=0&protocol=0&an3=3&sp1=1&sp2=2&sort=3&system=1&distinct=0&rettype=1&seprator=%0D%0A"
# PROXY = True
#
# TIMEOUT = 20

# geolocation
GOOGLE_API_KEY = "AIzaSyBuvFKna_9YqhszzmGNV1MIFjGNnfz8uyk"
# wang yu cheng
# AIzaSyBuvFKna_9YqhszzmGNV1MIFjGNnfz8uyk - MyProject
# AIzaSyAEo5rsZstUuAg5ybhXe8B8HbV60fKv-QM - IPGeolocation1
# AIzaSyAyvxPWCX-s2CrEoww7_wonrKPWTrEktCc - IPGeolocation2
# AIzaSyCKKnJG27lYn8irlFU692Z4Yqxu9W7iEOk - 4
# AIzaSyAoB92oqYcChkEiyKEwvDflmvDcH3RzdrA - 5

# wang xu
# AIzaSyBBdxZIv7AmVLNT3-VoePq9o22fvyyEy5Y - 9
# AIzaSyBlqR311Rwas43z7pOdtqu11mITiE1-fJc - 1
IP_INFO_IPIP_PATH = "../Sources/ip_gb_en.datx"


# measurement by keycdn
DRIVER_WAITING_TIME = 60

# measurement by Ripe
RIPE_KEY_O = "4a2268a2-17ad-42ea-9f82-16a92d0efeb5"
RIPE_ACCOUNT_KEY = [
    {
        "account": "wychengpublic@163.com",
        "key": "4a2268a2-17ad-42ea-9f82-16a92d0efeb5",
    },
    {
        "account": "minshanhou9@163.com",
        "key": "afec0a43-fd05-46e8-ab73-56cf34b2d0d6",
    },
    {
        "account": "pi8108548@163.com",
        "key": "57c65e56-8eae-407d-b538-5ecc29241f24",
    },
    {
        "account": "zhaijutong62@163.com",
        "key": "572494df-e7da-4db6-81cc-4583c2679c1d",
    },
    {
        "account": "suan4489055@163.com",
        "key": "be751041-9952-446c-8318-4f478a1c77a3",
    },
    {
        "account": "manggen418803@163.com",
        "key": "7620b0bb-d225-4812-89f1-6b65cd017cf4",
    },
    {
        "account": "huaisundian63@163.com",
        "key": "89745391-f1ce-44df-bc14-3280a1c33db5",
    },
    {
        "account": "jiyao7641607@163.com",
        "key": "75d5b2ed-a835-463a-91ca-a57da5541465",
    },
    {
        "account": "laideng26731@163.com",
        "key": "ec7fa793-3495-4b8e-8ab1-be482f6bff0d",
    },
    {
        "account": "tuan25370@163.com",
        "key": "35754fc0-3222-4485-a377-0cc960e376a1",
    },
]

# ocr tool
BAIDU_API_KEY = "24.41d0976869d7ae95714d188117a8b17c.2592000.1542006180.282335-14421471"
BAIDU_API_OCR_GENERAL = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
BAIDU_API_OCR_ACCURATE = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"

# ner tool
STOP_WORDS = ["Web Design", "www", "xxx", "Terms & Conditions", "ICP", "CMS", "PHP", "Contact Us", "jQuery", "edu",
              "Inc.", "Inc", "Ltd", "LLC", "L.L.C", "Ltd.", "Co.", "company", "incorporated", "Corporation"]

# frequent RegEx
PATTERN_COPYRIGHT = "((c|C)opyright|&copy;|©|\(c\)|（c）)"

# radius & distance
RADIUS_FOR_SEARCHING_CANDIDATES = 50000
MAX_DIS_WITHIN_A_SINGLE_ORG = 2000
MIN_DIS_BTW_DIF_COARSE_LOCS = 20000

# organization key word
ORG_KEYWORDS = ["college", "company", "university", "school", "corporation",
                "institute", "organization", "association"]

# default get_proxies_fun
from Doraemon.Requests import proxies_dora
FUN_GET_PROXIES = None
