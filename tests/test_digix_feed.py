import json
import pytest

from pricemonitor.config import Coin
from pricemonitor.producing.feed_prices import DigixFeed, DigixFeedError

from util.network import DataFormat, NetworkError

DGX_COIN = Coin(symbol="DGX", address="0x000", name="Digix Gold", volatility=0.05)
ETH_COIN = Coin(symbol="ETH", address="0x001", name="Ether", volatility=0.05)


class FailingNetwork:
    @staticmethod
    async def get_response_content_from_get_request(*args, **kwargs):
        raise NetworkError()


class FixedNetwork:
    async def get_response_content_from_get_request(self, *args, **kwargs):
        return json.loads(
            """
{
  "status": "success",
  "data": [
    {
      "symbol": "DGXETH",
      "price": 0.36043707,
      "time": 1548156049
    },
    {
      "symbol": "ETHUSD",
      "price": 115.18,
      "time": 1548156049
    },
    {
      "symbol": "ETHSGD",
      "price": 156.76,
      "time": 1548156049
    },
    {
      "symbol": "DGXUSD",
      "price": 41.52,
      "time": 1548156049
    },
    {
      "symbol": "EURUSD",
      "price": 1.13583,
      "time": 1548156049
    },
    {
      "symbol": "USDSGD",
      "price": 1.36101,
      "time": 1548156049
    },
    {
      "symbol": "XAUUSD",
      "price": 1283.78,
      "time": 1548156049
    },
    {
      "symbol": "USDJPY",
      "price": 109.457,
      "time": 1548156049
    }
  ]
}
"""
        )


def test_initial():
    feed = DigixFeed(coins=[DGX_COIN], market=ETH_COIN, network_access=FailingNetwork())


@pytest.mark.asyncio
async def test_get_price__network_raises_NetworkError__raises_DigixFeedError():
    feed = DigixFeed(coins=[DGX_COIN], market=ETH_COIN, network_access=FailingNetwork())

    with pytest.raises(DigixFeedError):
        await feed.get_price()


@pytest.mark.asyncio
async def test_get_price():
    feed = DigixFeed(coins=[DGX_COIN], market=ETH_COIN, network_access=FixedNetwork())

    res = await feed.get_price()

    assert res.pair == (DGX_COIN, ETH_COIN)
    assert res.price == 0.3583476769393404
