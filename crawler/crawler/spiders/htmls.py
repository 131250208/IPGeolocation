import scrapy
import json


class SchoolsSpider(scrapy.Spider):
    name = "htmls"

    def start_requests(self):
        list_school = json.load(open("../resources/school_us_0.4.json", "r"))
        for sch in list_school:
            yield scrapy.Request(url=sch["url"], callback=self.parse, meta={"sch": sch})

    def parse(self, response):
        if response.text != "":
            sch = response.meta["sch"]
            sch["html"] = response.text
            yield sch