import json
from collections import namedtuple

from pycoin.serialize import h2b

Coin = namedtuple("Coin", "symbol, address, name, volatility")


class Config:
    _MARKET_SYMBOL = "ETH"

    #_CONTRACT_ABI_PATH = "smart-contracts/contracts/abi/SanityRates.abi"
    _CONTRACT_ABI_PATH = "smart-contracts/contracts/abi/SanityRatesGasPrice.abi"

    def __init__(
        self,
        configuration_file_path,
        coin_volatility,
        contract_address,
        network,
        private_key=None,
    ):
        self.network = network
        self.contract_address = contract_address
        self._configuration_file_path = configuration_file_path
        self._coin_volatility = coin_volatility
        self._config = self._load_config()
        self.private_key = h2b(private_key)
        self.market = self._prepare_coin_from_config_token(
            symbol=Config._MARKET_SYMBOL,
            params=self._config['tokens'][Config._MARKET_SYMBOL]
        )
        self.coins = [
            self._prepare_coin_from_config_token(symbol=symbol, params=params)
            for symbol, params in self._config['tokens'].items()
            if self._filter_market_coin(symbol)
            and self._filter_internaly_used_coins(params)
        ]

    def _filter_market_coin(self, symbol):
        return symbol != self.market.symbol

    @staticmethod
    def _filter_internaly_used_coins(params):
        return params["internal use"]

    def _prepare_coin_from_config_token(self, symbol, params) -> Coin:
        return Coin(
            symbol=symbol,
            address=params["address"],
            name=params["name"],
            volatility=self._coin_volatility.get(symbol, Config._MARKET_SYMBOL),
        )

    @staticmethod
    def get_smart_contract_abi():
        with open(Config._CONTRACT_ABI_PATH) as contract_abi_file:
            return contract_abi_file.read()

    def _load_config(self):
        with open(self._configuration_file_path) as config_file:
            return json.load(config_file)
