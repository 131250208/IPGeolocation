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

REDUNDANT_LIST_QUERY = ["logo", "footer", "header", "body", "foot", "head", "brand", "smaller", "bigger", "text",
                       "home", "login", "system", "official site", "welcome", "main", "Inc.", "LLC", ".com"]

BlACK_LIST_LOGO = ["button", "btn", "login", "submit"]

REDUNDANT_LIST_COPYRIGHT = ["Infringement", "Privacy Statement", "Privacy Policy", "Disclaimer", "Nondiscrimination",
                        "All Rights Reserved", "Copyright", "Supported by", "NSF", "Site Policies", "Site Contact"
                        "Phone", "Fax", "Site Contact"]

# invalid Planetlab landmarks
INVALID_LANDMARKS = ["Oklahoma State University (Tulsa)", "University of California, Riverside",
                    "HP Labs", "University of Central Florida - EECS", "Northeastern University CCIS", "George Mason University",
                    "Dartmouth College, Computer Science", "Georgetown University", "Google", "University of Rochester", "University of Connecticut",
                    "University of California at Santa Barbara", "McGill University", "University of California, Davis",
                    "New York Institute of Technology", "Oregon State University School of Electrical Engineering and Computer Science",
                    "University of Delaware", "Iowa State University Electrical and Computer Engineering",
                    "University of Southern California, ISI", "North Carolina State University",# (4.8)
                    "Orbit", "Johns Hopkins CNDS", "Loyola University Chicago", "University of Florida - ACIS Lab",
                    "San Jose State University", "Packet Clearing House - San Francisco",
                     ]
# > 5000
# INVALID_LANDMARKS = ['HP Labs', 'University of Central Florida - EECS', 'Northeastern University CCIS', 'University of California, Riverside', 'University of California at Santa Barbara', 'HP Labs', 'Google', 'University of Rochester', 'University of California, Davis', 'University of Delaware', 'University of Southern California, ISI', 'Loyola University Chicago', 'University of Florida - ACIS Lab', 'San Jose State University']

# > 3000
# INVALID_LANDMARKS = ['HP Labs', 'University of Michigan', 'NEC Laboratories', 'University of Central Florida - EECS', 'Northeastern University CCIS', 'University of California, Riverside', 'University of California at Santa Barbara', 'HP Labs', 'Google', 'Rutgers University', 'University of Rochester', 'University of Connecticut', 'University of California, Davis', 'University of Wisconsin', 'New York Institute of Technology', 'University of Delaware', 'University of Southern California, ISI', 'University of Georgia', 'University of Nebraska - Lincoln', 'Loyola University Chicago', 'University of Florida - ACIS Lab', 'University of California, Irvine', 'San Jose State University', 'University of Washington - Accretive DSL', 'North Carolina State University']
INVALID_LANDMARKS_KEYWORD = ["MLab", "MeasurementLab",]
# 结点并没有部署在本地，机构地址和结点定位相距超过5KM， -1机构不在节点当前city, 查一查ISP是不是云服务商，查一查确切地址确认是搜索不成功还是真的不在本地
# HP Labs, University of Central Florida - EECS, Northeastern University CCIS, George Mason University(-1),
# Dartmouth College, Georgetown University, Google, University of Rochester, University of Connecticut
# University of California at Santa Barbara, McGill University, University of California, Davis,
# New York Institute of Technology, Oregon State University School of Electrical Engineering and Computer Science
# University of Delaware, Iowa State University Electrical and Computer Engineering
# University of Southern California, ISI, North Carolina State University(4.8)
# Orbit, Johns Hopkins CNDS, Loyola University Chicago, University of Florida - ACIS Lab
# San Jose State University, Packet Clearing House - San Francisco(*), University of California, Riverside

# 提供了多个ip结点，但只提供了一个站点（机构主页），无法确定在pl上的结点地址对应哪一个ip， 并且没有部署在本地(结点本地搜索不到该机构)
# MLab - DFW06、MLab - LGA0T， MLab - LGA0T， MLab - IAD0T，。。。  MeasurementLab

# 机构当地有多个定位
# University of California, Riverside

# 链接网页过期
# Oklahoma State University (Tulsa)


# 论文示例
# http://www.ittc.ku.edu/的logo
