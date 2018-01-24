class CoinVolatility:
    def get(self, coin_symbol, market):
        raise NotImplementedError()


class CoinVolatilityFixed(CoinVolatility):
    def __init__(self, volatility_value):
        self._volatility_value = volatility_value

    def get(self, coin_symbol, market):
        return self._volatility_value
