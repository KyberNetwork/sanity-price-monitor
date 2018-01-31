import json
from collections import namedtuple

from pycoin.serialize import h2b

Coin = namedtuple('Coin', 'symbol, address, name, volatility')


class Config:
    _MARKET_SYMBOL = 'ETH'

    # TODO: add option to read from environment variable
    _PRIVATE_KEY_PATH = '../KEY.json'

    # TODO: get actual contract from submodule
    _CONTRACT_ABI_PATH = 'storing/contract.abi'

    # TODO: get from actual contract
    SANITY_ADDRESS = '5735d385811e423D0E33a93861E687AEb590a00A'

    def __init__(self, configuration_file_path, coin_volatility):
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