import json
import logging

log = logging.getLogger(__name__)


class CoinVolatility:
    def get(self, coin_symbol, market):
        raise NotImplementedError()


class CoinVolatilityFile(CoinVolatility):
    def __init__(self, volatility_file_path, default_value):
        self._default_value = default_value
        with open(volatility_file_path) as data:
            self._values = json.load(data)

    def get(self, coin_symbol, market):
        try:
            return self._values['markets'][market][coin_symbol]
        except KeyError:
            log.info(f'Missing expected volatility for {coin_symbol}/{market}. Using default: {self._default_value}.')
            return self._default_value


class CoinNotDefined(RuntimeError):
    pass
