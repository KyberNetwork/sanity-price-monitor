import asyncio

from pricemonitor.datasource.exchanges import Exchange, ExchangeName


class ExchangePriceMonitor:
    def __init__(self, coins, market):
        self._coins = coins
        self._market = market
        self._exchanges = [
            Exchange.get_exchange(name)
            for name in [ExchangeName.BINANCE, ExchangeName.BITTREX]
        ]

    async def monitor(self, loop):
        coin_prices = await self._get_coin_prices(self._coins, self._market, loop)

        from pprint import pprint
        pprint(coin_prices)

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
        price_calls = (
            exchange.get_last_trades_average_or_last_trade(coin=coin, market=market)
            for exchange in self._exchanges
        )
        prices_values = [
            price
            for price in await asyncio.gather(*price_calls, loop=loop)
            if price is not None
        ]
        average_price = sum(prices_values) / len(prices_values)

        return (coin, market), average_price
