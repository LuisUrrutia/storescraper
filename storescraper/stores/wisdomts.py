import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import KEYBOARD, MONITOR, NOTEBOOK
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Wisdomts(Store):
    @classmethod
    def categories(cls):
        return [
            KEYBOARD,
            MONITOR,
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['accessories', KEYBOARD],
            ['monitores', MONITOR],
            ['computadores', NOTEBOOK]
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://wisdomts.cl/tienda/?yith_wcan=1' \
                          '&product_cat={}'.format(url_extension)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('ul', 'products')[-1]

            for container in product_containers.findAll(
                    'li', 'product-grid-view'):
                product_url = container.find('a')['href']
                if '2021-dell-gold-partner' in product_url:
                    continue
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # price_titles = [tag for tag in soup.findAll('h4')
        #                 if tag.find('strong')]
        #
        # assert len(price_titles) == 2
        #
        # price_tags = [tag.find('strong') for tag in price_titles]
        # offer_price = Decimal(
        #     remove_words(price_tags[0].text.replace('-', '')))
        # normal_price = Decimal(
        #     remove_words(price_tags[1].text.replace('-', '')))
        json_data = json.loads(
            soup.findAll('script', {'type': 'application/ld+json'})[1].text)
        product_data = json_data['@graph'][1]

        if product_data['offers'][0]['availability'] == \
                'http://schema.org/InStock':
            stock = -1
        else:
            stock = 0

        picture_urls = [product_data['image']]
        sku = str(product_data['sku'])
        name = product_data['name']
        description = product_data['description']
        price = Decimal(product_data['offers'][0]['price'])
        normal_price = offer_price = price

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )
        return [p]
