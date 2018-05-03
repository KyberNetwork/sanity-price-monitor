from typing import List

from pricemonitor.config import Coin
from pricemonitor.producing.data_producer import DataProducer, PairPrice
from pricemonitor.producing.exchange_prices import ExchangePrices
from pricemonitor.producing.feed_prices import FeedPrices


class AllTokenPrices(DataProducer):
    def __init__(self, coins: List[Coin], market: Coin, exchange_data_action=None) -> None:
        super().__init__(coins=coins, market=market)

        # TODO: use data from JSON to call with cex coins and feed coins separately
        self._exchange_prices = ExchangePrices(coins=coins, market=market, exchange_data_action=exchange_data_action)
        self._feed_prices = FeedPrices(coins=coins, market=market)

    async def get_data(self, loop) -> List[PairPrice]:
        return await self._exchange_prices.get_data(loop) + await self._feed_prices.get_data(loop)
