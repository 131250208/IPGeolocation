import scrapy
import re


class UniversitiesSpider(scrapy.Spider):
    name = "universities"

    def start_requests(self):
        urls = [
            'https://en.wikipedia.org/wiki/Lists_of_American_institutions_of_higher_education',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        uni_states = response.css("a[title*='List of colleges and universities']::attr('href')").extract()
        for next_sta in uni_states:
            url_next = response.urljoin(next_sta)
            search_group = re.search("List_of_colleges_and_universities_in_(.*)", url_next)
            yield scrapy.Request(url_next, callback=self.parse_state, meta={"state_name": re.sub("_", " ", search_group.group(1))})

    blacklist = ["See also", "References", "External links", "Defunct", "Out-of-state", "Key", "Notes", ]

    def parse_state(self, response):
        list_table = response.css("table")
        state_name = response.meta["state_name"]
        for table in list_table:
            caption = "".join(table.css("caption::text").extract())

            h2 = table.xpath("preceding-sibling::h2[1]") # find the last h2
            if len(h2) == 0:
                continue
            h2_text = "".join(h2.css("::text").extract())

            title = caption + " " + h2_text

            pattern_black = "(%s)" % "|".join(self.blacklist)
            if re.search(pattern_black, title, flags=re.I): # filter invalid table whose title includes keywords
                continue

            list_tr = table.css("tr")
            for row in list_tr[1:]:
                try:
                    uni_name = row.css("td,th")[0].css("::text").extract()[0] # extract uni name in every row
                except IndexError:
                    continue
                yield {"state_name": state_name, "university_name": uni_name.strip("\n")}

        list_ul = response.css("ul")
        for ul in list_ul:
            h2 = ul.xpath("preceding-sibling::h2[1]")  # find the last h2
            if len(h2) == 0:
                continue
            h2_text = "".join(h2.css("::text").extract())

            pattern_black = "(%s)" % "|".join(self.blacklist)
            if re.search(pattern_black, h2_text, flags=re.I):  # filter invalid table whose h2 includes keywords
                continue

            list_li = ul.css("li")
            for li in list_li:
                if len(li.css("ul")) > 0:
                    continue

                uni_str = li.css("::text").extract()
                yield {"state_name": state_name, "university_name": uni_str[0].strip("\n")}

