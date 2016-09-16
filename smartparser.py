from msp_scraper_lib.abstract import(
    BaseParser,
    ParserMixin
)
from msp_scraper_lib.helpers import scrape
from bs4 import BeautifulSoup
from msp_scraper_lib.results import SmartPriceSeller


class MappedListParser(BaseParser, ParserMixin):
    @property
    def get_paged_url(self):
        i = self.url.find(self.mapper)
        paged_url = '{}pages/{}'.format(self.url[:i], self.url[i:])
        return paged_url


class PriceListParser(BaseParser, ParserMixin):
    @property
    def get_paged_url(self):
        search_term = '/pricelist/'
        i = self.url.find(search_term) + len(search_term)
        paged_url = '{}pages/{}'.format(self.url[:i], self.url[i:])
        return paged_url


class SearchParser(BaseParser, ParserMixin):
    @property
    def get_paged_url(self):
        return self.url


# SCRAPE SELLERS
class SellerParser(object):
    def __init__(self, url, *args, **kwargs):
        print url
        self.url = url
        self.response = scrape(self.url, **kwargs)
        self.soup = BeautifulSoup(self.response, 'lxml')
        self.result = [
            SmartPriceSeller(self.get_product_attrs(item))
            for item in self.products_html
            ]

    def get_product_attrs(self, item):
        return dict(
            logo=item.find('img', {'class': 'prc-grid__logo'}).get('src'),
            name=item.find('img', {'class': 'prc-grid__logo'}).get('alt'),
            price=item.find('span', attrs={'class': 'prc-grid__prc-val'}).text,
            rating=item.get('data-rating'),
            color=item.get('data-color').split(';')
        )

    @property
    def products_html(self):
        html = self.soup.findAll(
            'div', attrs={'class': 'prc-grid clearfix'})
        return html
