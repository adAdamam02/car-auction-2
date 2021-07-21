import time
import scrapy
from scrapy.crawler import CrawlerRunner
from crochet import setup, wait_for
from datetime import datetime

setup()

info = []
date_time = 0

class CarSpider(scrapy.Spider):
    name = "cars"

    start_urls = [
        'https://bringatrailer.com/auctions/',
    ]

    def parse(self, response):
        global info
        global date_time

        current_time = time.time()
        date_time = datetime.fromtimestamp(current_time)

        cars = response.css('h3.auctions-item-title ::text').getall()
        links = response.css('.auctions-item-title a::attr(href)').getall()
        six_day_price = response.css('div.auctions-item-container::attr(data-price)').getall()
        time_remaining = [(int(x) - current_time) / 86400 for x in response.xpath('//span/strong/span').css('::attr(data-until)').getall()]

        if not (len(cars) == len(links) == len(list(six_day_price)) == len(list(time_remaining))):
            print("\n\n************* Scraped data items are not the same length *************\n\n")
            print(len(cars), len(links), len(six_day_price), len(list(time_remaining)))
            raise Exception

        info = list(filter(lambda x: x[2] != '' and int(x[2]) < 100000 and 5.0003 < x[3] <= 6, zip(cars, links, six_day_price, time_remaining)))

@wait_for(timeout=10.0)
def run_spider():
    crawler = CrawlerRunner()
    crawler.crawl(CarSpider)

def car_info():
    run_spider()
    for i in range(1000):
        if info != []:
            break

        time.sleep(0.01)

    return (info, date_time)

    