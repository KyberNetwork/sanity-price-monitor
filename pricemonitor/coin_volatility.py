import json
import logging

from pricemonitor.exceptions import PriceMonitorException, ConfigurationFileMissing

log = logging.getLogger(__name__)


class CoinVolatility:
    def get(self, coin_symbol, market):
        raise NotImplementedError()


class CoinVolatilityFile(CoinVolatility):
    def __init__(self, volatility_file_path):
        try:
            with open(volatility_file_path) as data:
                self._values = json.load(data)
        except FileNotFoundError as e:
            raise ConfigurationFileMissing("Missing coin volatility file.") from e

    def get(self, coin_symbol, market):
        try:
            return self._values["markets"][market][coin_symbol]
        except KeyError:
            log.info(f"Missing expected volatility for {coin_symbol}/{market}.")
            raise CoinNotDefined(
                "Expected volatility not defined for coin.",
                market=market,
                coin=coin_symbol,
            )


class CoinNotDefined(RuntimeError, PriceMonitorException):
    def __init__(self, msg, market, coin):
        super().__init__(f"{msg} ({coin}/{market}).")
        self.market = market
        self.coin = coin
