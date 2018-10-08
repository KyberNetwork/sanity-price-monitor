import asyncio
import logging
from collections import namedtuple
from enum import Enum
from typing import Optional, Set, Tuple

import ccxt.async as ccxt

from pricemonitor.config import Coin
from util.time import minutes_ago_in_millis_since_epoch

log = logging.getLogger(__name__)

ExchangeData = namedtuple('ExchangeData', ['name', 'config'])


class ExchangeName(Enum):
    BINANCE = ExchangeData(name=ccxt.binance, config={})
    BITTREX = ExchangeData(name=ccxt.bittrex, config={})
    HUOBI = ExchangeData(name=ccxt.huobipro, config={'enableRateLimit': True})


class Exchange:
    def __init__(self, exchange_name: ExchangeName) -> None:
        self._exchange = exchange_name.value.name(exchange_name.value.config)
        self._supported_markets = None  # type: Optional[Set[Tuple[str, str]]]

    @classmethod
    async def create(cls, exchange_name):
        exchange = cls(exchange_name)
        await exchange.update_supported_markets()
        return exchange

    async def get_last_trade_price(self, coin: Coin, market: Coin) -> Optional[float]:
        if not self._verify_supported(coin, market):
            # TODO: raise exception instead of returning None
            return None

        try:
            trades = await self._exchange.fetch_trades(symbol=_prepare_symbol(coin, market), limit=1)
            return trades[0]['price']
        except Exception as e:
            log.debug(e)
            # TODO: raise exception instead of returning None
            return None

    async def get_average_of_trades_last_minute(self, coin: Coin, market: Coin) -> Optional[float]:
        return await self._get_trades_average(coin=coin, market=market, since=minutes_ago_in_millis_since_epoch(1))

    async def get_last_minute_trades_average_or_last_trade(self, coin: Coin, market: Coin) -> Optional[float]:
        last_trades_average = await self.get_average_of_trades_last_minute(coin, market)

        if last_trades_average is not None:
            return last_trades_average

        log.debug(f'Could not get last minute trades, fetching last trade'
                  + f'({self._exchange.name}: {coin.symbol}/{market.symbol})')
        return await self.get_last_trade_price(coin, market)

    async def get_volatility(self, coin: Coin, market: Coin, time_period_in_minutes: float) -> Optional[float]:
        """ Calculates the change (in percentage) between the max and min price over previous X minutes """
        if not self._verify_supported(coin, market):
            # TODO: raise exception instead of returning None
            return None

        try:
            trades = await self._exchange.fetch_trades(
                symbol=_prepare_symbol(coin, market), since=minutes_ago_in_millis_since_epoch(time_period_in_minutes))
        except Exception as e:
            log.warning(e)
            # TODO: raise exception instead of returning None
            return None

        if not trades:
            log.info(
                f"No trades for {coin}/{market} in {self._exchange.name} during past {time_period_in_minutes} minutes")
            return 0

        trade_prices = [trade['price'] for trade in trades]

        max_price = max(trade_prices)
        min_price = min(trade_prices)
        return abs((max_price - min_price) / max_price) * 100

    async def _get_trades_average(self,
                                  coin: Coin,
                                  market: Coin,
                                  limit: int = None,
                                  since: float = None
                                  ) -> Optional[float]:
        if not self._verify_supported(coin, market):
            # TODO: raise exception instead of returning None
            return None

        try:
            trades = await self._exchange.fetch_trades(symbol=_prepare_symbol(coin, market), limit=limit, since=since)
        except Exception as e:
            log.debug(e)
            # TODO: raise exception instead of returning None
            return None

        prices = [
            trade['price']
            for trade in trades
        ]
        # TODO: raise exception instead of returning None
        return sum(prices) / len(prices) if prices else None

    def _verify_supported(self, coin: Coin, market: Coin) -> bool:
        return (coin.symbol, market.symbol) in self._supported_markets

    async def _get_supported_markets(self) -> Set[Tuple[str, str]]:
        markets = await self._exchange.load_markets()
        market_set = {
            tuple(coins.split('/'))
            for coins in markets.keys()
        }
        return market_set

    async def update_supported_markets(self) -> None:
        log.info(f'Updating supported markets for {self._exchange.name}')
        self._supported_markets = await self._get_supported_markets()


def _prepare_symbol(coin: Coin, market: Coin) -> str:
    return f'{coin.symbol}/{market.symbol}'


async def _test(loop):
    binance = Exchange(ExchangeName.BITTREX)
    for i in range(20):
        print(await binance.get_last_minute_trades_average_or_last_trade(coin='OMG', market='ETH'))
        await asyncio.sleep(1)


if __name__ == '__main__':
    log = logging.getLogger(__name__)
    log.info('Starting event loop')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_test(loop))
    finally:
        log.info('Closing event loop')
        loop.close()
