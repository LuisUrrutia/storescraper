import json
from decimal import Decimal
import logging

from bs4 import BeautifulSoup

from storescraper.categories import WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Woow(Store):
    @classmethod
    def categories(cls):
        return [
            WASHING_MACHINE
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extension = [
            WASHING_MACHINE
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for local_category in url_extension:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + local_category)
                url_webpage = 'https://shop.tata.com.uy/lg/lg?_q=lg&fuzzy=0' \
                    '&initialMap=ft&initialQuery=lg&map=brand,ft&operator=a' \
                    'nd&page={}'.format(page)
                max_tries = 0
                while max_tries < 3:
                    try:
                        data = session.get(url_webpage).text
                        soup = BeautifulSoup(data, 'html.parser')
                        json_data = json.loads(soup.findAll(
                            'script', {'type': 'application/ld+json'})[1].text)
                        break
                    except Exception as e:
                        print(e)
                        max_tries += 1
                item_list = json_data['itemListElement']
                if len(item_list) == 0:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                else:
                    for i in item_list:
                        product_urls.append(i['url'].replace(
                            'https://portal.vtexcommercestable.com.br/', ''))
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        soup_jsons = soup.findAll(
            'script', {'type': 'application/ld+json'})
        if len(soup_jsons) == 0 or not soup_jsons[0].text:
            return []
        json_data = json.loads(soup_jsons[0].text)
        name = json_data['name']
        sku = str(json_data['sku'])

        stock = 0
        if soup.find('div', 'vtex-add-to-cart-button-0-x-buttonDataContainer'):
            stock = -1

        price = Decimal(
            json_data['offers']['offers'][0]['price']
        )
        picture_urls = [tag['src'] for tag in
                        soup.find(
                            'div',
                            'vtex-store-components-3-x-'
                            'productImagesGallerySlide'
                            ).findAll('img')
                        ]
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
            'UYU',
            sku=sku,
            picture_urls=picture_urls
        )
        return [p]
