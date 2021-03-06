from gevent.threadpool import ThreadPool
from bs4 import BeautifulSoup

from msp_scraper_lib.results import SmartPriceResult
from msp_scraper_lib.helpers import scrape, scrape_helper
from msp_scraper_lib import constants


class BaseParser(object):
    def __init__(self, mapper, **kwargs):
        self.mapper = mapper
        self.params = kwargs
        self.url = None
        
        if self.mapper in constants.URL_MAPPER :
            self.url = constants.URL_MAPPER[self.mapper]
        else :
            self.url = self.mapper[len(constants.SMARTPRICE_WEB_URL):]

        self.response = scrape(self._make_url(self.url), **kwargs)
        self.soup = BeautifulSoup(self.response, 'lxml')
        self.result = [
            SmartPriceResult(self.get_product_attrs(item))
            for item in self.products_html
            ]

    def _make_url(self, target):
        return '{}{}'.format(constants.SMARTPRICE_WEB_URL, target)

    @property
    def price_results(self):
        if self.get_page_range:
            return self.process_multiple_pages()

        return self.result


class ParserMixin(object):
    def get_product_attrs(self, item):
        return dict(
            img=item.find('img').get('src').encode('utf-8'),
            title=item.find('a', attrs={'class': 'prdct-item__name'}).text.encode('utf-8'),
            url=item.find(
                'a', attrs={'class': 'prdct-item__name'}).get('href').encode('utf-8'),
            best_price=item.find(
                'span', attrs={'class': 'prdct-item__prc-val'}).text.encode('utf-8'),
            product_id=item.get('data-mspid').encode('utf-8')
        )

    @property
    def products_html(self):
        html = self.soup.findAll('div', attrs={'class': 'prdct-item'})
        return html

    def process_multiple_pages(self):
        results = self.result
        first_page, last_page = self.get_page_range
        paged_url = self.get_paged_url
        page_urls = []

        for page in range(first_page+1, last_page+1):
            url = paged_url.replace('.html', '-{}.html'.format(page))
            params = self.params.copy()
            if self.params.get('page', None):
                params.update({'page': page})
            page_urls.append((self._make_url(url), params))

        # Scrape pages in parallel
        pool = ThreadPool(20)
        i = 0

        for page in pool.map(scrape_helper, page_urls):
            self.soup = BeautifulSoup(page, 'lxml')

            results += [
                SmartPriceResult(self.get_product_attrs(item))
                for item in self.products_html
                ]
        return results

    @property
    def get_page_range(self):
        page_range = self.soup.findAll(
            'span', attrs={'class': 'pgntn__rslt-page'})

        if not page_range:
            return None

        first_page = int(page_range[0].text)
        last_page = int(page_range[1].text)
        return first_page, last_page

