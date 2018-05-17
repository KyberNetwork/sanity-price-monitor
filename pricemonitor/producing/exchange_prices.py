import asyncio
import time
from typing import List

from pricemonitor.producing.data_producer import DataProducer, PairPrice
from pricemonitor.producing.exchanges import Exchange, ExchangeName
from util.calculations import calculate_average


def calculate_seconds_left_to_sleep(start_time: float, interval_in_milliseconds: int) -> float:
    time_now = time.time()
    next_iteration_time = start_time + interval_in_milliseconds
    return (next_iteration_time - time_now) / 1_000


class ExchangePrices(DataProducer):
    _DEFAULT_EXCHANGES = [
        ExchangeName.BINANCE,
        ExchangeName.BITTREX,
        ExchangeName.HUOBI
    ]

    def __init__(self, coins, market, exchanges=None, exchange_data_action=None) -> None:
        super().__init__(coins=coins, market=market)

        if exchanges is None:
            exchanges = self._DEFAULT_EXCHANGES

        self._exchange_data_action = exchange_data_action

        # TODO: save exchange.fetch_markets() to ask an exchange for supported pairs only
        self._exchanges = [
            Exchange.get_exchange(name)
            for name in exchanges
        ]

    async def get_data(self, loop) -> List[PairPrice]:
        return await self._get_data_for_multiple_coins(self._exchange_data_action, loop)

    async def _get_data_for_multiple_coins(self, exchange_data_action, loop) -> List[PairPrice]:
        coin_prices_calculations = (
            self._get_data_for_single_coin(
                coin=coin,
                market=self._market,
                loop=loop,
                exchange_data_action=exchange_data_action)
            for coin in self._coins
        )
        coin_prices = await asyncio.gather(*coin_prices_calculations, loop=loop)
        return coin_prices

    # TODO: filter pairs that are not traded on the exchange
    async def _get_data_for_single_coin(self, coin, market, loop, exchange_data_action) -> PairPrice:
        exchange_api_calls = (
            exchange_data_action(exchange, coin=coin, market=market)
            for exchange in self._exchanges
        )
        data_from_all_exchanges = [
            value
            for value in await asyncio.gather(*exchange_api_calls, loop=loop)
            if value is not None
        ]

        return PairPrice(pair=(coin, market), price=calculate_average(data_from_all_exchanges))
