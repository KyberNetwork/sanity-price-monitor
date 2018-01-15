import asyncio
import logging
from enum import Enum

import ccxt.async as ccxt

from util.time import minutes_ago_in_millis_since_epoch

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)


class ExchangeName(Enum):
    BINANCE = ccxt.binance
    BITTREX = ccxt.bittrex


class Exchange:
    def __init__(self, exchange):
        self._exchange = exchange

    async def get_last_trade_price(self, coin, market):
        try:
            trades = await self._exchange.fetch_trades(symbol=_prepare_symbol(coin, market), limit=1)
            return trades[0]['price']
        except Exception as e:
            log.warning(e)
            return None

    async def get_average_of_trades_last_minute(self, coin, market):
        return await self._get_trades_average(coin=coin, market=market, since=minutes_ago_in_millis_since_epoch(1))

    async def get_last_minute_trades_average_or_last_trade(self, coin, market):
        last_trades_average = await self.get_average_of_trades_last_minute(coin, market)

        if last_trades_average is not None:
            return last_trades_average

        return await self.get_last_trade_price(coin, market)

    async def get_volatility(self, coin, market, time_period_in_minutes):
        """ Calculates the change (in percentage) between the max and min price over previous X minutes """
        try:
            trades = await self._exchange.fetch_trades(
                symbol=_prepare_symbol(coin, market), since=minutes_ago_in_millis_since_epoch(time_period_in_minutes))
        except Exception as e:
            log.warning(e)
            return None

        if not trades:
            log.info(
                f"No trades for {coin}/{market} in {self._exchange.name} during past {time_period_in_minutes} minutes")
            return 0

        trade_prices = [trade['price'] for trade in trades]

        max_price = max(trade_prices)
        min_price = min(trade_prices)
        return abs((max_price - min_price) / max_price) * 100

    async def _get_trades_average(self, coin, market, limit=None, since=None):
        try:
            trades = await self._exchange.fetch_trades(symbol=_prepare_symbol(coin, market), limit=limit, since=since)
        except Exception as e:
            log.warning(e)
            return None

        prices = [
            trade['price']
            for trade in trades
        ]
        return sum(prices) / len(prices) if prices else None

    @staticmethod
    def get_exchange(name):
        return Exchange(name.value())


def _prepare_symbol(coin, market):
    return f'{coin}/{market}'


async def _test(loop):
    binance = Exchange.get_exchange(ExchangeName.BITTREX)
    for i in range(20):
        print(await binance.get_last_minute_trades_average_or_last_trade(coin='OMG', market='ETH'))
        await asyncio.sleep(1)


if __name__ == '__main__':
    log = logging.getLogger('main')
    log.info('Starting event loop')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_test(loop))
    finally:
        log.info('Closing event loop')
        loop.close()
