from decimal import Decimal
import json
import logging
from bs4 import BeautifulSoup
from storescraper.categories import ALL_IN_ONE, MONITOR, NOTEBOOK, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class OpcStore(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            ALL_IN_ONE,
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['outlet', NOTEBOOK],
            ['notebook-tradicional', NOTEBOOK],
            ['chromebook', NOTEBOOK],
            ['notebook-corporativo', NOTEBOOK],
            ['tablet', TABLET],
            ['all-in-one', ALL_IN_ONE],
            ['monitores', MONITOR],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('Page overflow: ' + url_extension)
                url_webpage = 'https://www.opcstore.cl/collections/{}?' \
                              'page={}'.format(url_extension, page)
                data = session.get(url_webpage).text
                soup = BeautifulSoup(data, 'html.parser')
                product_containers = soup.findAll('li', 'grid__item')
                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    product_urls.append(
                        'https://www.opcstore.cl' + product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key = soup.find('input', {'name': 'id'})['value']

        json_data = json.loads(soup.findAll(
            'script', {'type': 'application/ld+json'})[-1].text)

        name = json_data['name']
        sku = json_data['sku']
        description = json_data['description']

        if 'caja abierta' in name.lower():
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        price = Decimal(json_data['offers'][0]['price'])

        if soup.find('button', 'shopify-payment-button__button'):
            stock = -1
        else:
            stock = 0

        picture_urls = []
        picture_container = soup.find('div', 'product-media-modal__content')
        for i in picture_container.findAll('img'):
            picture_urls.append('https:' + i['src'])

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            price,
            price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            description=description,
            condition=condition
        )
        return [p]