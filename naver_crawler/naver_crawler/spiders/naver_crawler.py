import scrapy
from naver_crawler.items import NaverCrawlerItem
from datetime import date, datetime, timedelta
import re


def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta


date_list = []
for result in perdelta(date(2005, 1, 1), date(2017, 12, 31), timedelta(days=4)):
    date_list.append(result.strftime("%Y.%m.%d"))

dateS = date_list[:-1]
dateE = date_list[1:]


class NaverSpider(scrapy.Spider):
    name = "naver"

    def start_requests(self):
        start_url = 'https://search.naver.com/search.naver?&where=news&query=%EA%B8%88%EB%A6%AC&sm=tab_pge&sort=2&photo=0&field=0&reporter_article=&pd=3&ds=2005.01.01&de=2005.01.10&docid=&nso=so:da,p:from20050101to20050110,a:all&mynews=1&start=1&refresh_start=0'
        yield scrapy.Request(url=start_url, callback=self.ongoing_requests)

    #def ongoing_date_request(sefl, response):

    def ongoing_requests(self, response):
        num = response.xpath(
            '//*[@id="main_pack"]/div[2]/div[1]/div[1]/span/text()').get()
        num = re.findall('[0-9]+,[0-9]+', num)
        num = int(re.sub(",", "", num[0]))
        urls = []
        start_num = (num // 10)*10 + 10
        for i, j in zip(dateS, dateE):
            for start in range(1, start_num, 10):
                urls.append("https://search.naver.com/search.naver?&where=news&query=%EA%B8%88%EB%A6%AC&sm=tab_pge&sort=2&photo=0&field=0&reporter_article=&pd=3&ds={}&de={}&docid=&nso=so:da,p:from20050101to20050110,a:all&mynews=1&start={}&refresh_start=0"
                            .format(i, j, start)
                            )
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse_page)

    def parse_page(self, response):
        articles = response.xpath("//dd[@class='txt_inline']")
        urls = []
        for article in articles:
            if (article.xpath("./span[@class='_sp_each_source']/text()").get().
                    strip() == "연합뉴스"):
                urls.extend(article.xpath("./a/@href").extract())
            elif (article.xpath("./span[@class='_sp_each_source']/text()").get().
                    strip() == "연합인포맥스"):
                urls.extend(article.xpath("./a/@href").extract())
            elif (article.xpath("./span[@class='_sp_each_source']/text()").get().
                    strip() == "이데일리"):
                urls.extend(article.xpath("./a/@href").extract())
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        item = NaverCrawlerItem()
        item['url'] = response.url
        item['content'] = response.xpath(
            "//div[@id='articleBodyContents']//text()").getall()
        item['media'] = response.xpath(
            "//div[@class='press_logo']/a/img/@alt").get()
        yield item
