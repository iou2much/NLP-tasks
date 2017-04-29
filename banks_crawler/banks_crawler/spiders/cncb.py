# -*- coding: utf-8 -*-
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.selector import Selector
from banks_crawler.items import BanksCrawlerItem
#import json
import re
#import sys
#from datetime import datetime
#reload(sys)
from bs4 import BeautifulSoup
#sys.setdefaultencoding('utf-8')


class CncbSpider(Spider):
    name = "cncb"
    allowed_domains = ["www.cncbinternational.com"]
    start_urls = (
            'https://www.cncbinternational.com/personal/investments/securities-trading-service-guide-and-faq/tc/index.jsp',
            'https://www.cncbinternational.com/personal/investments/securities-trading-service-guide-and-faq/en/index.jsp',
            'https://www.cncbinternational.com/personal/investments/securities-trading-service-guide-and-faq/sc/index.jsp'
    )
    re_lang = re.compile('/(\w+)?/index.jsp')
    #logger = logging.getLogger('scrapy.spidermiddlewares.httperror')
    #logger.setLevel(logging.WARNING)


    def parse(self, response):
        sel = Selector(response)
        lang = self.re_lang.findall(response.url)

        cate= sel.xpath('//div[@class="citicPageBodyContentWithNav"]/div[@class="row"]//div[@class="column column23"]//h3/text()').extract()[0]
        container = sel.xpath('//div[@class="citicPageBodyContentWithNav"]/div[@class="row"]//div[@class="JSTaccordion"]')

        for qna in container.xpath('div[@class="JSTaccordionNode"]|h3'):
            if 'h3' == qna.xpath('name()').extract()[0]:
                cate = qna.xpath('text()').extract()[0]
                continue
            quest = qna.xpath('div[@class="JSTaccordionHeading"]/ol/li/text()').extract()[0]
            ans = "".join(qna.xpath('div[@class="JSTaccordionContent"]/*').extract())
            soup = BeautifulSoup(ans)

            item = BanksCrawlerItem()
            item['category'] = cate
            item['question']=quest
            item['answer']=soup.get_text()
            item['language']=lang[0]
            yield(item)
