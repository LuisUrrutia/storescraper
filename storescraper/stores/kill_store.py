import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import MOTHERBOARD, PROCESSOR, RAM, \
    SOLID_STATE_DRIVE, VIDEO_CARD, MONITOR, KEYBOARD_MOUSE_COMBO, \
    COMPUTER_CASE, EXTERNAL_STORAGE_DRIVE, POWER_SUPPLY, HEADPHONES, \
    CPU_COOLER, GAMING_CHAIR, NOTEBOOK, VIDEO_GAME_CONSOLE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class KillStore(Store):
    @classmethod
    def categories(cls):
        return [
            MOTHERBOARD,
            PROCESSOR,
            RAM,
            SOLID_STATE_DRIVE,
            VIDEO_CARD,
            MONITOR,
            KEYBOARD_MOUSE_COMBO,
            COMPUTER_CASE,
            EXTERNAL_STORAGE_DRIVE,
            POWER_SUPPLY,
            HEADPHONES,
            CPU_COOLER,
            GAMING_CHAIR,
            NOTEBOOK,
            VIDEO_GAME_CONSOLE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['computacion/componentes/placas-madre', MOTHERBOARD],
            ['computacion/componentes/procesadores', PROCESSOR],
            ['computacion/componentes/memoria-ram', RAM],
            ['computacion/componentes/discos-internos', SOLID_STATE_DRIVE],
            ['computacion/componentes/tarjetas-de-video', VIDEO_CARD],
            ['computacion/monitores', MONITOR],
            ['computacion/mouse-y-teclado', KEYBOARD_MOUSE_COMBO],
            ['componentes/fuentes', POWER_SUPPLY],
            ['componentes/gabinetes', COMPUTER_CASE],
            ['computacion/almacenamiento/discos-externos',
             EXTERNAL_STORAGE_DRIVE],
            ['audio/audifonos', HEADPHONES],
            ['computacion/componentes/refrigeracion-y-ventiladores',
             CPU_COOLER],
            ['Computacion/Sillas', GAMING_CHAIR],
            ['computacion/notebooks', NOTEBOOK],
            ['Gaming', VIDEO_GAME_CONSOLE],
        ]
        session = session_with_proxy(extra_args)
        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            page = 1
            while True:
                if page > 20:
                    raise Exception('page overflow: ' + url_extension)
                url_webpage = 'https://www.killstore.cl/{}?page={}'.format(
                    url_extension, page)
                print(url_webpage)

                data = session.get(url_webpage).text
                page_state_text = re.search(r'__STATE__ = (.+)', data)
                page_state = json.loads(page_state_text.groups()[0])
                done = True

                for key, value in page_state.items():
                    if key.startswith('Product:') and 'linkText' in value:
                        product_urls.append('https://www.killstore.cl/' +
                                            value['linkText'] + '/p')
                        done = False

                if done:
                    break
                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        page_state_text = re.search(r'__STATE__ = (.+)', response.text)
        page_state = json.loads(page_state_text.groups()[0])
        name = sku = price = stock = picture_urls = part_number = None

        for state_key, value in page_state.items():
            if 'productId' in value:
                sku = value['productId']
            if 'productName' in value:
                name = value['productName']
            if 'Price' in value and '.kit' not in state_key:
                # print(foo)
                # print(json.dumps(value, indent=2))
                if price:
                    raise Exception('Repeated price entry')
                price = Decimal(value['Price'])
            if 'AvailableQuantity' in value:
                stock = value['AvailableQuantity']
            if 'productReference' in value:
                part_number = value['productReference']
            if 'images' in value:
                picture_urls = []
                for image_entry in value['images']:
                    image_id = image_entry['id'].split(':')[1]
                    picture_url = 'https://killstorecl.vtexassets.com/' \
                                  'arquivos/ids/' + image_id
                    picture_urls.append(picture_url)

        if price is None:
            return []

        assert name
        assert sku
        assert stock is not None

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
            part_number=part_number,
            picture_urls=picture_urls
        )
        return [p]
