import logging
import json

from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import TELEVISION
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Multimax(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 0
        page_size = 10
        while True:
            if page >= 20:
                raise Exception('Page overflow')

            url_webpage = 'https://searchserverapi.com/getresults?restrictBy' \
                '%5Bvendor%5D=LG&startIndex={}&api_key=8b0u9V' \
                '5d8D'.format(page*page_size)

            data = session.get(url_webpage).text
            json_data = json.loads(data)

            assert json_data['itemsPerPage'] == page_size

            items = json_data['items']

            if len(items) == 0:
                if page == 1:
                    logging.warning('Empty category')
                break

            for item in items:
                product_urls.append('https://www.multimax.net' + item['link'])

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1', 'product_name').text.strip()
        sku = soup.find('div', 'clearfix')['data-product-id']
        stock = -1
        price = Decimal(soup.find('div', 'modal_price subtitle').find('span',
                                                                      'money')
                        .text.replace('$', '').replace(',', ''))
        picture_urls = ['https:' + tag['src'] for tag in soup.find('div',
                                                                   'product-'
                                                                   'gallery')
                        .findAll('img', 'lazyloaded')]
        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=picture_urls
        )

        return [p]
