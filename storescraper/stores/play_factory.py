from decimal import Decimal
import json
import logging
import validators

from bs4 import BeautifulSoup

from storescraper.categories import GAMING_CHAIR, \
    KEYBOARD_MOUSE_COMBO, MONITOR, MOTHERBOARD, MOUSE, KEYBOARD, \
    HEADPHONES, COMPUTER_CASE, PROCESSOR, RAM, SOLID_STATE_DRIVE, VIDEO_CARD, \
    POWER_SUPPLY, CPU_COOLER, STEREO_SYSTEM
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy


class PlayFactory(StoreWithUrlExtensions):
    url_extensions = [
        ['componentes/tarjeta-de-video', VIDEO_CARD],
        ['componentes/placa-madre', MOTHERBOARD],
        ['componentes/procesadores-componentes', PROCESSOR],
        ['componentes/almacenamiento', SOLID_STATE_DRIVE],
        ['componentes/memoria-ram', RAM],
        ['componentes/fuente-de-poder', POWER_SUPPLY],
        ['zona-gamer/teclados-zona-gamer', KEYBOARD],
        ['zona-gamer/audifonos-zona-gamer', HEADPHONES],
        ['zona-gamer/kit-teclado-mouse', KEYBOARD_MOUSE_COMBO],
        ['zona-gamer/mouse', MOUSE],
        ['zona-gamer/refrigeracion-y-ventilacion', CPU_COOLER],
        ['zona-gamer/parlantes', STEREO_SYSTEM],
        ['computacion/gabinetes-pc', COMPUTER_CASE],
        ['mobiliario/sillas-gamer-mobiliario', GAMING_CHAIR],
        ['imagen-y-video/monitores-para-pc', MONITOR],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)
            url_webpage = 'https://www.playfactory.cl/categoria-producto' \
                          '/{}/page/{}/'.format(url_extension, page)
            print(url_webpage)
            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            if '404!' in soup.text:
                break
            product_containers = soup.findAll(
                'li', 'product')
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_url = container.find(
                    'a',
                    'woocommerce-LoopProduct-link ' +
                    'woocommerce-loop-product__link'
                )['href']
                product_urls.append(product_url)
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

        if len(soup_jsons) <= 1:
            return []

        json_data = json.loads(soup_jsons[1].text)['@graph'][0]
        base_name = json_data['name']

        picture_urls = []
        figures = soup.find(
            'div', 'woocommerce-product-gallery__wrapper')
        for a in figures.findAll('img'):
            if validators.url(a['src']):
                picture_urls.append(a['src'])

        products = []
        variants_form = soup.find('form', 'variations_form cart')
        if variants_form:
            varaints_json = json.loads(
                variants_form['data-product_variations'])
            for variant in varaints_json:
                var_name = ""
                for key in variant['attributes']:
                    var_name += ' - ' + variant['attributes'][key]
                name = base_name + var_name
                offer_price = Decimal(variant['display_price'])
                normal_price = (offer_price * Decimal('1.025')).quantize(0)

                sku = variant['sku']
                stock = variant['max_qty']

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
                )
                products.append(p)

            return products
        else:
            sku = soup.find('button', 'single_add_to_cart_button')[
                'value'].strip()
            offer_price = Decimal(json_data['offers'][0]['price'])
            normal_price = (offer_price * Decimal('1.025')).quantize(0)
            stock = 0
            qty_input = soup.find('input', 'qty')
            if qty_input:
                if 'type' in qty_input.attrs and qty_input['type'] == "hidden":
                    stock = 1
                elif 'max' in qty_input.attrs and qty_input['max'] != "":
                    stock = int(qty_input['max'])
                else:
                    stock = 1

            p = Product(
                base_name,
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
            )
            return [p]
