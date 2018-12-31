from theo.framework import Component, System
from theo.src.trade.Kiwoom import Kiwoom


class KiwoomCtrl(Component):
    def initial(self):
        self.log.print('info', 'initial')

        self.kiwoom = Kiwoom()

        System.register_interface('KiwoomCtrl', 'get_accounts', [0], self.get_accounts)

        System.register_interface('KiwoomCtrl', 'get_markets', [0], self.get_markets)
        System.register_interface('KiwoomCtrl', 'get_codes', [1], self.get_codes)
        System.register_interface('KiwoomCtrl', 'get_price_types', [2], self.get_price_types)

        System.register_interface('KiwoomCtrl', 'get_item', [2], self.get_item)
        System.register_interface('KiwoomCtrl', 'get_prices', [3, 4], self.get_prices)

    def get_accounts(self):
        return self.kiwoom.get_accounts()

    def get_markets(self):
        return self.kiwoom.get_markets()

    def get_codes(self, market):
        return self.kiwoom.get_codes(market)

    def get_price_types(self, market, code):
        return self.kiwoom.get_price_types(market, code)

    def get_item(self, market, code):
        return self.kiwoom.get_item(market, code)

    def get_prices(self, market, code, price_type, range=None):
        return self.kiwoom.get_prices(market, code, price_type, range)
