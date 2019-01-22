import pytest
import json

from pricemonitor.config import Coin
from pricemonitor.producing.feed_prices import BtcFeed, BtcFeedError

from util.network import DataFormat, NetworkError

WBTC_COIN = Coin(symbol="WBTC", address="0x000", name="WrappedBitcoin", volatility=0.05)
ETH_COIN = Coin(symbol="ETH", address="0x001", name="Ether", volatility=0.05)


class FailingNetwork:
    @staticmethod
    async def get_response_content_from_get_request(*args, **kwargs):
        raise NetworkError()


class FixedNetwork:
    def __init__(self, price: float) -> None:
        self._price = price

    async def get_response_content_from_get_request(self, url, *args, **kwargs):
        return json.loads(
            f"""
{{
  "trade_id": 6610681,
  "price": "{self._price}",
  "size": "0.10000000",
  "time": "2019-01-22T10:12:22.844Z",
  "bid": "0.03292",
  "ask": "0.03293",
  "volume": "5136.39874555"
}}
"""
        )


class MissingPriceNetwork:
    async def get_response_content_from_get_request(self, url, *args, **kwargs):
        return json.loads(
            """
{
  "trade_id": 6610681,
  "size": "0.10000000",
  "time": "2019-01-22T10:12:22.844Z",
  "bid": "0.03292",
  "ask": "0.03293",
  "volume": "5136.39874555"
}
"""
        )


class ErrorPriceFormatNetwork:
    async def get_response_content_from_get_request(self, url, *args, **kwargs):
        return json.loads(
            """
{
  "trade_id": 6610681,
  "price": "banana",
  "size": "0.10000000",
  "time": "2019-01-22T10:12:22.844Z",
  "bid": "0.03292",
  "ask": "0.03293",
  "volume": "5136.39874555"
}
"""
        )


@pytest.mark.asyncio
async def test_get_price__network_raises_NetworkError__raises_BtcFeedError():
    feed = BtcFeed(coins=[WBTC_COIN], market=ETH_COIN, network_access=FailingNetwork())

    with pytest.raises(BtcFeedError):
        await feed.get_price()


@pytest.mark.asyncio
async def test_get_price__feed_price_is_half__returns_2():
    feed = BtcFeed(coins=[WBTC_COIN], market=ETH_COIN, network_access=FixedNetwork(0.5))

    res = await feed.get_price()

    assert res.pair == (WBTC_COIN, ETH_COIN)
    assert res.price == 2


@pytest.mark.asyncio
async def test_get_price__feed_price_is_tenth__returns_10():
    feed = BtcFeed(coins=[WBTC_COIN], market=ETH_COIN, network_access=FixedNetwork(0.1))

    res = await feed.get_price()

    assert res.pair == (WBTC_COIN, ETH_COIN)
    assert res.price == 10


@pytest.mark.asyncio
async def test_get_price__feed_price_missing__raises_BtcFeedError():
    feed = BtcFeed(
        coins=[WBTC_COIN], market=ETH_COIN, network_access=MissingPriceNetwork()
    )

    with pytest.raises(BtcFeedError):
        await feed.get_price()


@pytest.mark.asyncio
async def test_get_price__feed_price_not_float__raises_BtcFeedError():
    feed = BtcFeed(
        coins=[WBTC_COIN], market=ETH_COIN, network_access=ErrorPriceFormatNetwork()
    )

    with pytest.raises(BtcFeedError):
        await feed.get_price()
