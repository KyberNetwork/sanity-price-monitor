import json
from collections import namedtuple

Coin = namedtuple('Coin', 'symbol, address, name')


class Config:
    _MARKET_SYMBOL = 'ETH'

    # TODO: put in a configuration file
    _PRIVATE_KEY_PATH = '../KEY.json'

    def __init__(self, configuration_file_path):
        self._configuration_file_path = configuration_file_path
        self._config = self._load_config()
        self.market = self._prepare_coin_from_config_token(
            symbol=Config._MARKET_SYMBOL, params=self._config['tokens'][Config._MARKET_SYMBOL])
        self.coins = [
            self._prepare_coin_from_config_token(symbol=symbol, params=params)
            for symbol, params in self._config['tokens'].items()
            if symbol != self.market.symbol
        ]

    def get_admin_private(self):
        with open(Config._PRIVATE_KEY_PATH) as key_file:
            key_data = json.load(key_file)
            return key_data['private']

    def _load_config(self):
        with open(self._configuration_file_path) as config_file:
            return json.load(config_file)

    @staticmethod
    def _prepare_coin_from_config_token(symbol, params):
        return Coin(symbol=symbol, address=params['address'], name=params['name'])
