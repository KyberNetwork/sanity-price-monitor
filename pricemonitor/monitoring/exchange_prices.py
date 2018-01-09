import asyncio
import time

from pricemonitor.datasource.exchanges import Exchange, ExchangeName
from util.calculations import calculate_average


def calculate_seconds_left_to_sleep(start_time, interval_in_milliseconds):
    time_now = time.time()
    next_iteration_time = start_time + interval_in_milliseconds
    return (next_iteration_time - time_now) / 1_000


class ExchangePriceMonitor:
    def __init__(self, coins, market, exchanges=None):
        if exchanges is None:
            exchanges = [ExchangeName.BINANCE, ExchangeName.BITTREX]

        self._coins = coins
        self._market = market
        self._exchanges = [
            Exchange.get_exchange(name)
            for name in exchanges
        ]

    async def monitor(self, exchange_data_action, monitor_action, interval_in_milliseconds, loop):
        while True:
            start_time = time.time()

            coin_prices = await self._get_coin_prices(
                coins=self._coins, market=self._market, loop=loop, exchange_data_action=exchange_data_action)
            monitor_action.act(coin_prices)

            await asyncio.sleep(calculate_seconds_left_to_sleep(start_time, interval_in_milliseconds), loop=loop)

    async def _get_coin_prices(self, coins, market, loop, exchange_data_action):
        coin_prices_calculations = [
            self._get_average_price(coin=coin, market=market, loop=loop, exchange_data_action=exchange_data_action)
            for coin in coins
        ]
        coin_prices = await asyncio.gather(
            *(price_calculation for price_calculation in coin_prices_calculations), loop=loop)
        return coin_prices

    # TODO: filter pairs that are not traded on the exchange
    async def _get_average_price(self, coin, market, loop, exchange_data_action):
        exchange_api_calls = (
            exchange_data_action(exchange, coin=coin, market=market)
            for exchange in self._exchanges
        )
        coin_prices_from_all_exchanges = [
            price
            for price in await asyncio.gather(*exchange_api_calls, loop=loop)
            if price is not None
        ]

        return (coin, market), calculate_average(coin_prices_from_all_exchanges)
