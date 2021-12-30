import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, PRINTER, MONITOR, \
    STORAGE_DRIVE, HEADPHONES, KEYBOARD, WEARABLE, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class NotebooksYa(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            PRINTER,
            MONITOR,
            STORAGE_DRIVE,
            HEADPHONES,
            KEYBOARD,
            WEARABLE,
            ALL_IN_ONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['portatiles/?', NOTEBOOK],
            ['computadores/?', ALL_IN_ONE],
            ['impresion/?', PRINTER],
            ['pantallas-y-tvs/?', MONITOR],
            ['almacenamiento/?', STORAGE_DRIVE],
            ['partes-y-piezas/?', STORAGE_DRIVE],
            ['audifonos/?', HEADPHONES],
            ['audio-y-video/?', HEADPHONES],
            ['teclados-mouse/?', KEYBOARD],
            ['relojes/?', WEARABLE],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 10:
                    raise Exception('page overflow: ' + url_extension)

                url_webpage = 'https://notebooksya.cl/{}&wpf_page={}'.format(
                    url_extension, page)
                print(url_webpage)

                response = session.get(url_webpage)
                soup = BeautifulSoup(response.text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers:
                    if page == 1:
                        logging.warning('Empty category: ' + url_extension)
                    break
                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in product_urls:
                        return product_urls
                    product_urls.append(product_url)
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find('h1', 'product_title'):
            name = soup.find('h1', 'product_title').text
        else:
            name = soup.find('div', 'et_pb_module et_pb_wc_title '
                                    'et_pb_wc_title_0 '
                                    'et_pb_bg_layout_light').text.strip()
        sku = soup.find('button', {'name': 'add-to-cart'})['value']
        stock = int(soup.find('p', 'stock').text.split()[0])
        price_container = soup.find('div', 'wds').findAll('bdi')
        normal_price = Decimal(remove_words(price_container[0].text))
        offer_price = Decimal(remove_words(price_container[1].text))
        picture_urls = [tag['src'] for tag in soup.find('div',
                        'woocommerce-product-gallery').findAll('img')]
        description = soup.find(
            'meta', {'property': 'og:description'})['content']

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