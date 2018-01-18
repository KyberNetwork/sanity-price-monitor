import logging
from time import time

import pytest
from ccxt.base.errors import ExchangeError

from pricemonitor.config import Coin
from pricemonitor.datasource.exchanges import Exchange, ExchangeName

logging.disable(logging.WARNING)

COIN = Coin(symbol='KNC', address='0x000', name='KyberNetworkCrystal')
MARKET = Coin(symbol='ETH', address='0x001', name='Ether')


class CcxtExchangeWithSomeTrades:
    TRADES = [{'price': 100}, {'price': 200}, {'price': 300}, {'price': 400}, {'price': 500}]
    TRADES_AVERAGE = 300
    TRADES_VOLATILITY = 80

    async def fetch_trades(self, *args, **kwargs):
        return CcxtExchangeWithSomeTrades.TRADES


class CcxtExchangeNoTrades:
    def __init__(self):
        self.name = "TestDummy"

    async def fetch_trades(self, since, *args, **kwargs):
        return []


class CcxtExchangeNoTradesFromLastMinute:
    LAST_TRADE_PRICE = 1000
    LAST_TRADE = [{'price': LAST_TRADE_PRICE}]

    @staticmethod
    def _time_now_in_millis_from_epoch():
        return int(round(time() * 1_000))

    async def fetch_trades(self, since, *args, **kwargs):
        if self._time_now_in_millis_from_epoch() - since < 60 * 1_000:
            return []

        return CcxtExchangeNoTradesFromLastMinute.LAST_TRADE


class CcxtExchangeThatRaisesException:
    async def fetch_trades(self, *args, **kwargs):
        raise ExchangeError()


@pytest.mark.asyncio
async def test_get_last_trade_price():
    exchange = Exchange(CcxtExchangeWithSomeTrades())

    res = await exchange.get_last_trade_price(coin=COIN, market=MARKET)

    assert 100 == res


@pytest.mark.asyncio
async def test_get_last_trade_price__no_trades__returns_none():
    exchange = Exchange(CcxtExchangeNoTrades())

    res = await exchange.get_last_trade_price(coin=COIN, market=MARKET)

    assert res is None


@pytest.mark.asyncio
async def test_get_average_of_trades_last_minute():
    exchange = Exchange(CcxtExchangeWithSomeTrades())

    res = await exchange.get_average_of_trades_last_minute(coin=COIN, market=MARKET)

    assert CcxtExchangeWithSomeTrades.TRADES_AVERAGE == res


@pytest.mark.asyncio
async def test_get_last_minute_trades_average_or_last_trade__no_trades_from_last_minute__returns_last_trade():
    exchange = Exchange(CcxtExchangeNoTradesFromLastMinute())

    res = await exchange.get_last_minute_trades_average_or_last_trade(coin=COIN, market=MARKET)

    assert CcxtExchangeNoTradesFromLastMinute.LAST_TRADE_PRICE == res


@pytest.mark.asyncio
async def test_get_average_of_trades_last_minute__exception_raised__returns_none():
    exchange = Exchange(CcxtExchangeThatRaisesException())

    res = await exchange.get_average_of_trades_last_minute(coin=COIN, market=MARKET)

    assert res is None


@pytest.mark.asyncio
async def test_get_average_of_trades_last_minute__no_trades__returns_none():
    exchange = Exchange(CcxtExchangeNoTrades())

    res = await exchange.get_average_of_trades_last_minute(coin=COIN, market=MARKET)

    assert res is None


@pytest.mark.asyncio
async def test_get_last_trade_price__exception_raised__returns_none():
    exchange = Exchange(CcxtExchangeThatRaisesException())

    res = await exchange.get_last_trade_price(coin=COIN, market=MARKET)

    assert res is None


@pytest.mark.asyncio
async def test_get_last_minute_trades_average_or_last_trade__exception_raised__returns_none():
    exchange = Exchange(CcxtExchangeThatRaisesException())

    res = await exchange.get_last_minute_trades_average_or_last_trade(coin=COIN, market=MARKET)

    assert res is None


@pytest.mark.asyncio
async def test_get_volatility__some_trades__returns_value():
    exchange = Exchange(CcxtExchangeWithSomeTrades())

    res = await exchange.get_volatility(coin=COIN, market=MARKET, time_period_in_minutes=1)

    assert CcxtExchangeWithSomeTrades.TRADES_VOLATILITY == res


@pytest.mark.asyncio
async def test_get_volatility__exception_raised__returns_none():
    exchange = Exchange(CcxtExchangeThatRaisesException())

    res = await exchange.get_volatility(coin=COIN, market=MARKET, time_period_in_minutes=1)

    assert res is None


@pytest.mark.asyncio
async def test_get_volatility__no_trades__returns_0():
    exchange = Exchange(CcxtExchangeNoTrades())

    res = await exchange.get_volatility(coin=COIN, market=MARKET, time_period_in_minutes=1)

    assert 0 == res


def test_get_exchange__returns_an_exchange():
    exchange = Exchange.get_exchange(ExchangeName.BITTREX)

    assert isinstance(exchange, Exchange)
