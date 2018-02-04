import json
import os
from collections import namedtuple

from pycoin.serialize import h2b

from pricemonitor.exceptions import PriceMonitorException

Coin = namedtuple('Coin', 'symbol, address, name, volatility')


class Config:
    _MARKET_SYMBOL = 'ETH'

    # TODO: add option to read from environment variable
    _PRIVATE_KEY_PATH = 'KEY.json'

    _CONTRACT_ABI_PATH = 'smart-contracts/contracts/abi/SanityRates.abi'

    # TODO: get from actual contract
    SANITY_ADDRESS = '5735d385811e423D0E33a93861E687AEb590a00A'

    def __init__(self, configuration_file_path, coin_volatility, private_key=None):
        self._configuration_file_path = configuration_file_path
        self._coin_volatility = coin_volatility
        self._config = self._load_config()
        self.market = self._prepare_coin_from_config_token(
            symbol=Config._MARKET_SYMBOL, params=self._config['tokens'][Config._MARKET_SYMBOL])
        self.coins = [
            self._prepare_coin_from_config_token(symbol=symbol, params=params)
            for symbol, params in self._config['tokens'].items()
            if symbol != self.market.symbol
        ]
        self._setup_private_key(private_key)

    @staticmethod
    def get_admin_private():
        with open(Config._PRIVATE_KEY_PATH) as key_file:
            key_data = json.load(key_file)
            private_key_str = key_data['private']
            return h2b(private_key_str)

    def _prepare_coin_from_config_token(self, symbol, params):
        return Coin(symbol=symbol,
                    address=params['address'],
                    name=params['name'],
                    volatility=self._coin_volatility.get(symbol, Config._MARKET_SYMBOL))

    @staticmethod
    def get_smart_contract_abi():
        with open(Config._CONTRACT_ABI_PATH) as contract_abi_file:
            return contract_abi_file.read()

    @staticmethod
    def get_smart_contract_address():
        return Config.SANITY_ADDRESS

    def _load_config(self):
        with open(self._configuration_file_path) as config_file:
            return json.load(config_file)

    def _setup_private_key(self, private):
        if private is None:
            private = self._read_private_key_from_env()

        if private is None:
            private = self._read_private_from_file()

        if private is None:
            raise MissingPrivateKey('Please configure private key in environment variable SANITY_PRIVATE_KEY or in '
                                    'Key.json file')

        self.private_key = h2b(private)

    @staticmethod
    def _read_private_key_from_env():
        private = os.environ.get("SANITY_PRIVATE_KEY")
        return private

    @staticmethod
    def _read_private_from_file():
        with open(Config._PRIVATE_KEY_PATH) as key_file:
            key_data = json.load(key_file)
            return key_data['private']


class MissingPrivateKey(RuntimeError, PriceMonitorException):
    pass
