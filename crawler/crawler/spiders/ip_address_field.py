import scrapy
import json
import re


class IpFieldSpider(scrapy.Spider):
    name = "ip_field"

    def start_requests(self):
        yield scrapy.Request(url="http://ip.bczs.net/country/US", callback=self.parse)

    def parse(self, response):
        list_a = response.css("table > tbody > tr > td > a[title*='美国IP地址段:']")
        for a in list_a:
            search_group = re.search("美国IP地址段:([0-9\.]+)-([0-9\.]+)", a.css("::attr(title)").extract_first())
            yield {"start": search_group.group(1),
                    "end": search_group.group(2)}