import logging

from util import network

log = logging.getLogger(__name__)


class PriceProvider:
    async def get_coin_prices(self, coins, market):
        raise NotImplementedError


class CryptoCompare(PriceProvider):
    _URL_PRICE_MULTI_FULL = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms={}&tsyms={}'

    async def get_coin_prices(self, coins, market):
        try:
            response = await network.get_json_response_from_request(self._prepare_coin_prices_query(coins, market))
        except Exception:
            log.exception('[Error] error while querying CryptoCompare')
            return None

        return self._extract_coin_prices_from_response(response, market)

    def _prepare_coin_prices_query(self, coins, market):
        return self.__class__._URL_PRICE_MULTI_FULL.format(prepare_parameter(coins), market)

    @staticmethod
    def _extract_coin_prices_from_response(response, market):
        return {
            f'{coin}/{market}': data[market]['PRICE']
            for coin, data in response['RAW'].items()
        }


def prepare_parameter(param):
    if isinstance(param, list):
        return ','.join(param)
    return param
