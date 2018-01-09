import asyncio
import logging
import time
from enum import Enum

import ccxt.async as ccxt

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)


class ExchangeName(Enum):
    BINANCE = ccxt.binance
    BITTREX = ccxt.bittrex


def time_last_minute_in_millis_since_epoch():
    return int(round(time.time() * 1_000)) - 60_000


class ExchangeError(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __repr__(self):
        return repr(self._msg)


class Exchange:
    def __init__(self, exchange):
        self._exchange = exchange

    async def get_last_trade_price(self, coin, market):
        try:
            trades = await self._exchange.fetch_trades(symbol=f'{coin}/{market}', limit=1)
            return trades[0]['price']
        except ccxt.ExchangeError as e:
            log.warning(e)
            return None

    async def get_trades_average(self, coin, market, limit=None, since=None):
        try:
            trades = await self._exchange.fetch_trades(symbol=f'{coin}/{market}', limit=limit, since=since)
        except ccxt.ExchangeError as e:
            log.warning(e)
            return None

        prices = [
            trade['price']
            for trade in trades
        ]
        return sum(prices) / len(prices) if len(prices) > 0 else None

    async def get_average_of_trades_last_minute(self, coin, market):
        return await self.get_trades_average(
            coin=coin, market=market, since=time_last_minute_in_millis_since_epoch())

    async def get_last_trades_average_or_last_trade(self, coin, market):
        last_trades_average = await self.get_average_of_trades_last_minute(coin, market)

        if last_trades_average is not None:
            return last_trades_average

        return await self.get_last_trade_price(coin, market)

    @staticmethod
    def get_exchange(name):
        return Exchange(name.value())


async def _test(loop):
    binance = Exchange.get_exchange(ExchangeName.BITTREX)
    for i in range(20):
        print(await binance.get_last_trades_average_or_last_trade(coin='OMG', market='ETH'))
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
