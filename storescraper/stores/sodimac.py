import json
import random

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Sodimac(Store):
    @classmethod
    def categories(cls):
        return [
            'WashingMachine',
            'Refrigerator',
            'Oven',
            'VacuumCleaner',
            'Lamp',
            'Television',
            'Notebook',
            'LightProjector',
            'AirConditioner',
            'WaterHeater',
            'Tablet',
            'SpaceHeater',
            'Cell',
            'Headphones',
            'StereoSystem',
            'Wearable'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['scat112555/Lavadoras', 'WashingMachine'],  # Lavadoras
            ['cat1590057/Lavadoras-secadoras', 'WashingMachine'],
            ['scat114994/Secadoras', 'WashingMachine'],  # Secadoras
            ['scat112543/Freezer', 'Refrigerator'],  # Freezer
            ['scat114992/No-Frost', 'Refrigerator'],  # No Frost
            ['scat535116/Side-by-Side', 'Refrigerator'],  # Side by Side
            ['scat114991/Frio-Directo', 'Refrigerator'],  # Frio directo
            ['scat112545/Frigobar', 'Refrigerator'],  # Frigobares
            ['cat4850051/Aspiradoras-portatiles', 'VacuumCleaner'],
            # Aspiradoras
            ['cat1580015/Hornos-Electricos', 'Oven'],  # Hornos electricos
            ['scat112547/Microondas', 'Oven'],  # Microondas
            ['cat360045/Ampolletas-LED', 'Lamp'],  # Ampolletas LED
            ['cat3810002/Televisores', 'Television'],  # Televisores
            ['cat3390002/Notebook', 'Notebook'],  # Notebooks
            ['cat2930160/Reflectores-LED', 'LightProjector'],  # Proyectores
            ['cat4780002/Aires-Acondicionados-Split', 'AirConditioner'],  # AC
            ['scat663002/Calefont-tiro-natural', 'WaterHeater'],
            ['cat2080050/Calefont-tiro-forzado', 'WaterHeater'],
            ['scat923316/Termos-electricos-hogar', 'WaterHeater'],
            ['scat918650/Calderas', 'WaterHeater'],
            # ['cat3620002/Tablet', 'Tablet'],
            ['scat583461/Estufas-Toyotomi', 'SpaceHeater'],
            # ['scat299492/Estufas-a-Gas', 'SpaceHeater'],
            ['scat411008/Estufas-a-Parafina', 'SpaceHeater'],
            # ['cat1560069/Termoventiladores', 'SpaceHeater'],
            # ['cat1560012/Estufas-Far-Infrared', 'SpaceHeater'],
            # ['cat1560071/Convectores', 'SpaceHeater'],
            ['cat1590078/Estufas-Tiro-Forzado', 'SpaceHeater'],
            ['scat301608/Estufas-a-Lena', 'SpaceHeater'],
            ['cat3870010/Smartphones', 'Cell'],
            ['cat3870001/Audifonos', 'Headphones'],
            # ['cat3870011/Audifonos-para-celulares', 'Headphones'],
            ['scat913770/Equipos-de-Musica', 'StereoSystem'],
            # ['cat4850257/Home-Theater-y-Soundbars', 'StereoSystem'],
            ['cat8350012/Parlantes-bluetooth', 'StereoSystem'],
            # ['cat4850400/Parlantes-y-Karaokes', 'StereoSystem'],
            ['cat8350014/Tornamesas', 'StereoSystem'],
            ['cat3870009/Wearables', 'Wearable']
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 0

            while True:
                url = 'https://www.sodimac.cl/sodimac-cl/category/{}?No={}' \
                      '&rnd={}'.format(category_path, page,
                                       random.randint(0, 100))
                print(url)

                response = session.get(url, timeout=30)

                if '/product/' in response.url:
                    product_urls.append(response.url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                mosaic_divs = soup.findAll('section', 'jq-item')

                if not mosaic_divs:
                    if page == 0:
                        raise Exception('No products for {}'.format(url))
                    break

                for div in mosaic_divs:
                    product_url = 'https://www.sodimac.cl/sodimac-cl/' \
                                  'product/' + div['data']
                    product_urls.append(product_url)
                page += 16

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        response = session.get(url, timeout=30)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        if soup.find('p', 'sinStock-online-p-SEO'):
            return []

        sku = soup.find('input', {'id': 'currentProductId'})['value'].strip()
        key = soup.find('input', {'id': 'currentSkuId'})['value'].strip()

        pricing_container = soup.find('div', {'id': 'JsonArray'})

        if soup.find('div', {'id': 'JsonArray'}):
            pricing_json = json.loads(pricing_container.text)[0]

            if 'EVENTO' in pricing_json:
                normal_price = Decimal(pricing_json['EVENTO'])
            elif 'MASBAJO' in pricing_json:
                normal_price = Decimal(pricing_json['MASBAJO'])
            elif 'INTERNET' in pricing_json:
                normal_price = Decimal(pricing_json['INTERNET'])
            else:
                return []

            if 'CMR' in pricing_json:
                offer_price = Decimal(pricing_json['CMR'])
                if offer_price > normal_price:
                    offer_price = normal_price
            else:
                offer_price = normal_price

            name = '{} {}'.format(pricing_json.get('brand', ''),
                                  pricing_json['name']).strip()

            stock_regex = r'{}=(\d+)'.format(key)
            stock_text = re.search(stock_regex,
                                   pricing_json['stockLevel']).groups()[0]
            stock = int(stock_text)
        else:
            stock = 0
            normal_price = Decimal(remove_words(
                soup.find('p', 'price').text.split('\xa0')[0]))
            offer_price = normal_price

            model = soup.find('h1', 'name').text
            brand = soup.find('h2', 'brand').text
            name = u'{} {}'.format(brand, model)

        description = '\n\n'.join([html_to_markdown(str(panel)) for panel in
                                   soup.findAll('section', 'prod-car')])

        # Pictures

        pictures_resource_url = 'https://sodimac.scene7.com/is/image/' \
                                'SodimacCL/{}?req=set,json'.format(sku)
        pictures_json = json.loads(
            re.search(r's7jsonResponse\((.+),""\);',
                      session.get(pictures_resource_url,
                                  timeout=30).text).groups()[0])

        picture_urls = []

        picture_entries = pictures_json['set']['item']
        if not isinstance(picture_entries, list):
            picture_entries = [picture_entries]

        for picture_entry in picture_entries:
            picture_url = 'https://sodimac.scene7.com/is/image/{}?scl=1.0' \
                          ''.format(picture_entry['i']['n'])
            picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
