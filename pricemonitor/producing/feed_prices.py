import logging
from abc import ABC, abstractmethod
from typing import List, Dict

from pricemonitor.config import Coin
from pricemonitor.exceptions import PriceMonitorException
from pricemonitor.producing.data_producer import DataProducer, PairPrice
from util import network
from util.functional import first
from util.network import DataFormat, NetworkError

log = logging.getLogger(__name__)


class Feed(ABC):
    @abstractmethod
    async def get_price(self) -> PairPrice:
        pass


class DigixFeed(Feed):
    _DIGIX_FEED_URL = "https://datafeed.digix.global/tick/"
    _OUNCE_TO_GRAM = 31.103_476_8

    def __init__(self, coins: List[Coin], market: Coin, network_access) -> None:
        self._market = market
        self._digix_coin = _find_coin("DGX", coins)
        self._network = network_access

    async def get_price(self) -> PairPrice:
        try:
            feed = await self._network.get_response_content_from_get_request(
                url=self._DIGIX_FEED_URL, format=DataFormat.JSON
            )
        except NetworkError as e:
            msg = f"Error getting Digix feed from {self._DIGIX_FEED_URL}"
            log.exception(msg)
            raise DigixFeedError(msg) from e
        else:
            return PairPrice(
                pair=(self._digix_coin, self._market),
                price=await self._calculate_xau_eth_price(feed),
            )

    async def _calculate_xau_eth_price(self, feed):
        xau_usd = self._get_price_from_feed(feed, "XAUUSD")
        eth_usd = self._get_price_from_feed(feed, "ETHUSD")
        value = (xau_usd / eth_usd) / self._OUNCE_TO_GRAM
        return value

    @staticmethod
    def _get_price_from_feed(feed: Dict, symbol) -> int:
        try:
            price_item = first(
                feed["data"], lambda feed_price: feed_price["symbol"] == symbol
            )
        except StopIteration:
            raise DigixFeedError(f"Missing fields in Digix feed, symbol: {symbol}")
        else:
            return price_item["price"]


class BtcFeed(Feed):
    """Get ETH -> BTC price from feed"""

    _BTC_FEED_URL = "https://api.pro.coinbase.com/products/eth-btc/ticker"

    def __init__(self, coins: Coin, market: Coin, network_access) -> None:
        self._btc = _find_coin("WBTC", coins)
        self._market = market
        self._network = network_access

    async def get_price(self) -> PairPrice:
        """Returns a PairPrice or raises an exception if operation failed"""
        try:
            data = await self._network.get_response_content_from_get_request(
                url=self._BTC_FEED_URL, format=DataFormat.JSON
            )
        except NetworkError as e:
            msg = f"Error getting BTC feed from {self._BTC_FEED_URL}"
            log.exception(msg)
            raise BtcFeedError() from e

        try:
            price = 1 / float(data["price"])
        except KeyError as e:
            msg = f"Missing price field in BTC feed from {self._BTC_FEED_URL}"
            log.exception(msg)
            raise BtcFeedError() from e
        except ValueError as e:
            msg = f"Error value in price field in BTC feed from {self._BTC_FEED_URL}: {data['price']}"
            log.exception(msg)
            raise BtcFeedError() from e

        return PairPrice(pair=(self._btc, self._market), price=price)


class FeedPrices(DataProducer):
    def __init__(self, coins: List[Coin], market: Coin) -> None:
        super().__init__(coins=coins, market=market)
        self._digix_feed = DigixFeed(coins=coins, market=market, network_access=network)
        self._btc_feed = BtcFeed(coins=coins, market=market, network_access=network)

    async def initialize(self) -> None:
        pass

    async def get_data(self, loop) -> List[PairPrice]:
        log.debug("Preparing feed data")
        data = [
            # TODO: generalize to handle other feed based tokens
            await self._digix_feed.get_price(),
            await self._btc_feed.get_price(),
        ]
        log.debug("Finished preparing feed data")
        return data


class DigixFeedError(Exception, PriceMonitorException):
    pass


class BtcFeedError(Exception, PriceMonitorException):
    pass


class CoinError(Exception, PriceMonitorException):
    pass


def _find_coin(symbol, coins):
    try:
        coin = first(coins, lambda coin: coin.symbol == symbol)
    except StopIteration:
        raise CoinError(f"Missing coin in config: {symbol}")
    else:
        return coin
