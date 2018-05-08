import itertools
import logging
from typing import List

from pricemonitor.config import Coin
from pricemonitor.exceptions import PriceMonitorException
from pricemonitor.producing.data_producer import DataProducer, PairPrice
from pricemonitor.producing.exchange_prices import ExchangePrices
from pricemonitor.producing.feed_prices import FeedPrices

log = logging.getLogger(__name__)


class AllTokenPrices(DataProducer):
    def __init__(self, coins: List[Coin], market: Coin, exchange_data_action=None) -> None:
        super().__init__(coins=coins, market=market)

        # TODO: use data from JSON to call with cex coins and feed coins separately
        self._exchange_prices = ExchangePrices(coins=coins, market=market, exchange_data_action=exchange_data_action)
        self._feed_prices = FeedPrices(coins=coins, market=market)

    async def initialize(self) -> None:
        await self._exchange_prices.initialize()
        await self._feed_prices.initialize()

    async def get_data(self, loop) -> List[PairPrice]:
        exchange_prices = await self._try_getting_prices(self._exchange_prices, loop)
        feed_prices = await self._try_getting_prices(self._feed_prices, loop)

        # TODO: return an itertools instead of list
        return list(itertools.chain(exchange_prices, feed_prices))

    @staticmethod
    async def _try_getting_prices(source: DataProducer, loop) -> List[PairPrice]:
        try:
            prices = await source.get_data(loop)
        except PriceMonitorException:
            log.exception('Error getting prices from source')
            prices = []
        return prices
