from pricemonitor.coin_volatility import CoinVolatilityFixed


def test_coinVolatilityFixed__initial():
    v = CoinVolatilityFixed(0.05)

    assert v is not None


def test_getVolatility__any_coin__fixed_volatility():
    v = CoinVolatilityFixed(0.05)

    coin_volatility = v.get('OMG', 'ETH')

    assert 0.05 == coin_volatility
