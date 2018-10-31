import scrapy
import re


class SchoolsSpider(scrapy.Spider):
    name = "schools"
    blacklist = ["See also", "References", "External links", "Defunct", "Out-of-state", "Key", "Notes", "Secretaries"]

    def start_requests(self):
        urls = [
            'https://en.wikipedia.org/wiki/Lists_of_schools_in_the_United_States',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        list_ul = response.css("h2~ul")
        for ul in list_ul:
            h2 = ul.xpath("preceding-sibling::h2[1]")  # find the last h2
            h2_text = "".join(h2.css("::text").extract())
            pattern_black = "(%s)" % "|".join(self.blacklist)
            if re.search(pattern_black, h2_text, flags=re.I):  # filter invalid ul whose title includes keywords
                continue

            list_li = ul.css("li")
            for li in list_li:
                list_a = li.css("a")
                state_name = list_a[0].css("::text").extract()[0]
                for a in list_a[1:]:
                    text = a.css("::text").extract()[0]
                    if "school districts" in text:
                        continue
                    # yield {"state_name": state_name, "url": a.css("::attr('href')").extract()[0]}
                    yield scrapy.Request(response.urljoin(a.css("::attr('href')").extract()[0]), callback=self.parse_state, meta={"state_name": state_name})

    def parse_state(self, response):
        state_name = response.meta["state_name"]

        list_table = response.css("table")
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
                yield {"state_name": state_name, "school_name": uni_name.strip("\n")}

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
                try:
                    yield {"state_name": state_name, "school_name": uni_str[0].strip("\n")}
                except IndexError:
                    continue