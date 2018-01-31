import json
import logging

log = logging.getLogger(__name__)


class CoinVolatility:
    def get(self, coin_symbol, market):
        raise NotImplementedError()


class CoinVolatilityFile(CoinVolatility):
    def __init__(self, volatility_file_path):
        with open(volatility_file_path) as data:
            self._values = json.load(data)

    def get(self, coin_symbol, market):
        try:
            return self._values['markets'][market][coin_symbol]
        except KeyError:
            log.info(f'Missing expected volatility for {coin_symbol}/{market}.')
            raise CoinNotDefined(market=market, coin=coin_symbol)


class CoinNotDefined(RuntimeError):
    def __init__(self, market, coin):
        super().__init__(f'Expected volatility not defined for {coin}/{market}.')
        self.market = market
        self.coin = coin
