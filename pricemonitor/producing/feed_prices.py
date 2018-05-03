from typing import List, Dict

from pricemonitor.config import Coin
from pricemonitor.exceptions import PriceMonitorException
from pricemonitor.producing.data_producer import DataProducer, PairPrice
from util import network
from util.functional import first
from util.network import DataFormat


class DigixFeed:
    _DIGIX_FEED_URL = 'https://datafeed.digix.global/tick/'
    _OUNCE_TO_GRAM = 31.1034768

    def __init__(self, digix_coin: Coin, market: Coin) -> None:
        self._market = market
        self._digix_coin = digix_coin

    async def get_price(self) -> PairPrice:
        feed = await network.get_response_content_from_get_request(url=self._DIGIX_FEED_URL,
                                                                   format=DataFormat.JSON)
        return PairPrice(pair=(self._digix_coin, self._market),
                         price=await self._calculate_xau_eth_price(feed))

    async def _calculate_xau_eth_price(self, feed):
        xau_usd = self._get_price_from_feed(feed, 'XAUUSD')
        eth_usd = self._get_price_from_feed(feed, 'ETHUSD')
        value = (xau_usd / eth_usd) / self._OUNCE_TO_GRAM
        return value

    @staticmethod
    def _get_price_from_feed(feed: Dict, symbol) -> int:
        try:
            price_item = first(feed['data'], lambda feed_price: feed_price['symbol'] == symbol)
        except StopIteration:
            raise DigixFeedError(f'Missing fields in Digix feed, symbol: {symbol}')
        else:
            return price_item['price']


def _find_digix_coin(coins):
    try:
        digix = first(coins, lambda coin: coin.symbol == 'DGX')
    except StopIteration:
        raise CoinError('Missing coin in config: DGX')
    else:
        return digix


class FeedPrices(DataProducer):
    def __init__(self, coins: List[Coin], market: Coin) -> None:
        super().__init__(coins=coins, market=market)
        self._digix_feed = DigixFeed(digix_coin=_find_digix_coin(coins), market=market)

    async def get_data(self, loop) -> List[PairPrice]:
        return [
            # TODO: generalize to handle other feed based tokens
            await self._digix_feed.get_price()
        ]


class DigixFeedError(Exception, PriceMonitorException):
    pass


class CoinError(Exception, PriceMonitorException):
    pass
