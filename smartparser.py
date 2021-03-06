from bs4 import BeautifulSoup
from urllib import unquote_plus
from pylev import levenshtein
from json import loads as json_decode

from msp_scraper_lib.abstract import(
    BaseParser,
    ParserMixin
)
from msp_scraper_lib.helpers import scrape
from msp_scraper_lib.constants import SMARTPRICE_WEB_URL, URL_MAPPER
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
        self.url = url
        self.response = scrape(self.url, **kwargs)
        self.soup = BeautifulSoup(self.response, 'lxml')
        self.result = [
            SmartPriceSeller(self.get_product_attrs(item))
            for item in self.products_html
            ]

    def get_product_attrs(self, item):
        price = item.find('span', attrs={'class': 'prc-grid__prc-val'}).text
        image = item.find('img', {'class': 'prc-grid__logo'})
        color = item.get('data-color')
        seller_url = item.find('div', attrs={'class': 'js-prc-tbl__gts-btn'})

        if seller_url :
            seller_url = seller_url.get('data-url')
            response = scrape(seller_url)
            soup = BeautifulSoup(response, 'lxml')
            seller_url = soup.find('a', attrs={'class' : 'store-link'}).get('href')

            if 'mysmartprice.go2cloud.org' in seller_url :
                search_string = '&url='
                index = seller_url.find(search_string) + len(search_string)
                seller_url = seller_url[index:]

        return dict(
            logo=(image.get('src').encode('utf-8') if image else None),
            name=(image.get('alt').encode('utf-8') if image else None),
            price=(price[1:] if price else price).encode('utf-8'),
            rating=item.get('data-rating').encode('utf-8'),
            color = (color.encode('utf-8') if color else color),
            url = seller_url
        )

    @property
    def products_html(self):
        html = self.soup.findAll(
            'div', attrs={'class': 'prc-grid clearfix'})
        return html


class MatchParser(object) :

    def __init__(self, search_key, *args, **kwargs) :
        self.url = SMARTPRICE_WEB_URL + URL_MAPPER['complete'] + '?term=' + search_key
        self.term = unquote_plus(search_key)
        self.response = scrape(self.url, **kwargs)
        try :
            self.response = json_decode(self.response)
        except Exception, e :
            print e
    
    def get_matching_url(self) :
        products = self.response.get('products')
        results = dict()

        for p in products :
            title = p.get('value') 
            ed = levenshtein(self.term, title)
            results[ed] = p.get('url')

        response = sorted(results)
        response = results.get(response[0])
        index = response.find('?')
        return response[:index]
