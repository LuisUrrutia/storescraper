import logging
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, MOUSE, MONITOR, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class SmartDeal(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []
        if category != NOTEBOOK:
            return []
        response = session.get('https://smartdeal.cl/tienda/')
        data = response.text
        soup = BeautifulSoup(data, 'html.parser')
        product_containers = soup.findAll('li', 'product')
        for container in product_containers:
            product_url = container.find('a')['href']
            product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('div', 'et_pb_module et_pb_wc_title '
                                'et_pb_wc_title_0_tb_body '
                                'et_pb_bg_layout_light').find('h1').text
        sku = soup.find('button', 'single_add_to_cart_button')['value']

        stock = int(soup.find('p', 'stock in-stock').text.split()[0])
        if soup.find('p', 'price').find('ins'):
            price = Decimal(
                remove_words(soup.find('p', 'price').find('ins').text))
        else:
            price = Decimal(remove_words(soup.find('p', 'price').text))
        if soup.find('div', 'et_pb_row et_pb_row_3_tb_body').findAll(
                'div', 'et_pb_text_inner')[1].text in ['Factory Refurbished']:
            condition = 'https://schema.org/RefurbishedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        picture_url = [tag['src'] for tag in
                       soup.find('div', 'woocommerce-product-gallery').findAll(
                           'img')]
        if soup.find('div', 'et_pb_row et_pb_row_3_tb_body').find('span',
                                                                  'sku'):
            part_number = soup.find('div', 'et_pb_row et_pb_row_3_tb_body'). \
                find('span', 'sku').text
        else:
            part_number = None

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
            'CLP',
            sku=sku,
            condition=condition,
            part_number=part_number,
            picture_urls=picture_url
            )
        return [p]
