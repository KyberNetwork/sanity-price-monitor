import asyncio
import time

from pricemonitor.datasource.exchanges import Exchange, ExchangeName


def _calculate_average(values):
    try:
        return sum(values) / len(values)
    except ZeroDivisionError:
        return None


def calculate_seconds_left_to_sleep(start_time, interval_in_milliseconds):
    time_now = time.time()
    next_iteration_time = start_time + interval_in_milliseconds
    return (next_iteration_time - time_now) / 1_000


class ExchangePriceMonitor:
    def __init__(self, coins, market):
        self._coins = coins
        self._market = market
        self._exchanges = [
            Exchange.get_exchange(name)
            for name in [ExchangeName.BINANCE, ExchangeName.BITTREX]
        ]

    async def monitor(self, price_update_handler, interval_in_milliseconds, loop):
        while True:
            start_time = time.time()

            coin_prices = await self._get_coin_prices(self._coins, self._market, loop)
            price_update_handler(coin_prices)

            await asyncio.sleep(calculate_seconds_left_to_sleep(start_time, interval_in_milliseconds), loop=loop)

    async def _get_coin_prices(self, coins, market, loop):
        coin_prices_calculations = [
            self._get_average_price(coin, market, loop)
            for coin in coins
        ]
        coin_prices = await asyncio.gather(
            *(price_calculation for price_calculation in coin_prices_calculations), loop=loop)
        return coin_prices

    # TODO: filter pairs that are not traded on the exchange
    async def _get_average_price(self, coin, market, loop):
        exchange_api_calls = (
            exchange.get_last_trades_average_or_last_trade(coin=coin, market=market)
            for exchange in self._exchanges
        )
        coin_prices_from_all_exchanges = [
            price
            for price in await asyncio.gather(*exchange_api_calls, loop=loop)
            if price is not None
        ]

        return (coin, market), _calculate_average(coin_prices_from_all_exchanges)
