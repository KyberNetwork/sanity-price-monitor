import pytest

from pricemonitor.coin_volatility import CoinVolatilityFile, CoinNotDefined


def test_coinVolatilityFile_getVolatility_setTo5percent__fivePercentReturned(tmpdir):
    coin_volatility_file_path = _get_coin_volatility_json_file(tmpdir)
    v = CoinVolatilityFile(coin_volatility_file_path)

    volatility = v.get(coin_symbol='OMG', market='ETH')

    assert 0.05 == volatility


def test_coinVolatilityFile_getVolatility_coinNotDefined__defaultValueReturned(tmpdir):
    coin_volatility_file_path = _get_coin_volatility_json_file(tmpdir)
    v = CoinVolatilityFile(coin_volatility_file_path)

    with pytest.raises(CoinNotDefined) as excinfo:
        v.get(coin_symbol='XXX', market='YYY')

    assert 'YYY' == excinfo.value.market
    assert 'XXX' == excinfo.value.coin


def _get_coin_volatility_json_file(tmpdir):
    f = tmpdir.join("coin_volatility.json")
    f.write('{"markets": {"ETH": {"OMG": 0.05}}}')
    return f.realpath()
