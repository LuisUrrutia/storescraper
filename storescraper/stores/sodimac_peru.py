from .falabella_peru import FalabellaPeru


class SodimacPeru(FalabellaPeru):
    seller = 'SODIMAC'

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = super(SodimacPeru, cls).products_for_url(
            url, category=category, extra_args=extra_args)
        for product in products:
            product.seller = None
        return products