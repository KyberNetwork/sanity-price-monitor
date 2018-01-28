import asyncio
import logging

from pricemonitor.storing.web3_connector import Web3ConnectionError

log = logging.getLogger(__name__)


class SanityContractUpdater:
    SET_RATES_FUNCTION_NAME = 'setSanityRates'
    GET_RATE_FUNCTION_NAME = 'getSanityRate'

    def __init__(self, web3_connector, config):
        self._web3 = web3_connector
        self._config = config
        self._rates_converter = ContractRateArgumentsConverter(self._config.market)
        self._updates_requested = 0

    async def update_prices(self, coin_price_data, loop):
        previous_rates = await self._get_previous_rates(loop)

        rates_for_update = self._prepare_rates_for_update(previous_rates=previous_rates, new_rates=coin_price_data)

        if rates_for_update:
            rs = await self.set_rates(rates_for_update, loop)
            self._updates_requested += 1
            return rs

        log_line = "No updates required.\n"
        # TODO: fix logging
        log.info(log_line)
        print(log_line)
        return None

    async def set_rates(self, coin_price_data, loop):
        rs = await self._web3.call_remote_function(
            function_name=SanityContractUpdater.SET_RATES_FUNCTION_NAME,
            args=(self._rates_converter.format_coin_prices_for_setter(coin_price_data)),
            loop=loop)
        return rs

    async def get_rate(self, coin, loop):
        try:
            local_function_response = await self._web3.call_local_function(
                function_name=SanityContractUpdater.GET_RATE_FUNCTION_NAME,
                args=(self._rates_converter.format_coin_for_getter(coin)),
                loop=loop)
            # A single value is returned
            rate_from_contract = local_function_response[0]
        except Web3ConnectionError:
            log.warning(f"Could not get current rate of {coin}. Assuming 0.")
            rate_from_contract = 0

        return self._rates_converter.convert_rate_from_contract_units(rate_from_contract)

    async def _get_pair_price_future(self, coin, loop):
        return (coin, self._config.market), await self.get_rate(coin, loop)

    async def _get_previous_rates(self, loop):
        previous_rate_futures = [
            asyncio.ensure_future(self._get_pair_price_future(coin, loop))
            for coin in self._config.coins
        ]
        previous_rates = await asyncio.gather(*previous_rate_futures, loop=loop)

        return {
            (coin, market): price
            for (coin, market), price in previous_rates
        }

    def _prepare_rates_for_update(self, previous_rates, new_rates):
        updates = []
        for (coin, market), price in new_rates:
            if self._should_update_price(coin,
                                         market,
                                         previous_rate=self._get_previous_rate(coin, market, previous_rates),
                                         current_rate=price):
                updates.append(((coin, market), price))

        return updates

    def _should_update_price(self, coin, market, previous_rate, current_rate):
        current_change = abs(current_rate - previous_rate) / previous_rate
        should_update = current_change > coin.volatility
        log_line = (f'{coin.symbol}/{market.symbol}:\t' +
                    f'previous={previous_rate:11.8}\t' +
                    f'current={current_rate:11.8}\t' +
                    f'change={current_change:11.5}\t' +
                    f'threshold={coin.volatility:11.5}\t' +
                    f'update={should_update}')
        # TODO: fix logging
        log.info(log_line)
        print(log_line)
        return should_update

    def _get_previous_rate(self, coin, market, rates):
        try:
            return rates[(coin, market)]
        except KeyError:
            return None


# TODO: test this class
class ContractRateArgumentsConverter:
    CHANGE_FACTOR = 10 ** 18

    def __init__(self, market):
        self._market = market

    @staticmethod
    def format_coin_prices_for_setter(coin_price_data):
        sources = []
        rates = []

        for (coin, market), price in coin_price_data:
            # TODO: should this code receive a None? Saw while running.
            if price:
                sources.append(coin.address)
                rates.append(ContractRateArgumentsConverter.convert_price_to_contract_units(price))

        return [sources, rates]

    def format_coin_for_getter(self, coin):
        return [coin.address, self._market.address]

    @staticmethod
    def convert_rate_from_contract_units(rate_from_contract):
        return rate_from_contract / ContractRateArgumentsConverter.CHANGE_FACTOR

    @staticmethod
    def convert_price_to_contract_units(price):
        """ Prices in the contract have some limitations.

        Prices are kept as a uint in the contract so we shift the decimal point a couple of places.
        e.g. A rate of OMG/ETH: 0.016883 means that one OMG costs 0.016883 ETH, and so the contract will be sent a rate
        of 16,883,000,000,000,000.
        """
        return round(price * ContractRateArgumentsConverter.CHANGE_FACTOR)
