import asyncio
import logging
from typing import List, Tuple, Dict, Optional

from pricemonitor.config import Coin, Config
from pricemonitor.producing.data_producer import PairPrice
from pricemonitor.storing.node_errors import PreviousTransactionPending
from pricemonitor.storing.web3_connector import Web3ConnectionError, Web3Connector

log = logging.getLogger(__name__)


class SanityContractUpdater:
    SET_RATES_FUNCTION_NAME = "setSanityRates"
    #GET_RATE_FUNCTION_NAME = "tokenRate"
    GET_RATE_FUNCTION_NAME = "sanityData"

    def __init__(self, web3_connector: Web3Connector, config: Config) -> None:
        self._web3 = web3_connector
        self._config = config
        self._rates_converter = ContractRateArgumentsConverter(self._config.market)
        self._updates_requested = 0

    async def update_prices(
        self, coin_price_data: List[PairPrice], loop, force: bool = False
    ) -> Optional[int]:
        previous_rates = await self._get_previous_rates(
            loop
        )  # type: Dict[Tuple[Coin, Coin], float]

        if force:
            rates_for_update = coin_price_data
        else:
            rates_for_update = self._prepare_rates_for_update(
                previous_rates=previous_rates, new_rates=coin_price_data
            )

        if rates_for_update:
            log.info(f"Update #{self._updates_requested}: {rates_for_update}")
            try:
                rs = await self.set_rates(rates_for_update, loop)
                self._updates_requested += 1
            except PreviousTransactionPending:
                # send request again with same nonce and a higher gas price
                rs = None

            return rs

        log.info("No updates required.\n")
        return None

    async def set_rates(self, coin_price_data: List[PairPrice], loop) -> int:
        rs = await self._web3.call_remote_function(
            function_name=SanityContractUpdater.SET_RATES_FUNCTION_NAME,
            eth_args=(
                self._rates_converter.format_coin_prices_for_setter(coin_price_data)
            ),
            loop=loop,
        )
        return rs

    async def get_rate(self, coin: Coin, loop) -> float:
        try:
            local_function_response = await self._web3.call_local_function(
                function_name=SanityContractUpdater.GET_RATE_FUNCTION_NAME,
                eth_args=(self._rates_converter.format_coin_for_getter(coin)),
                loop=loop,
            )
            # A single value is returned
            rate_from_contract = local_function_response[0]
        except Web3ConnectionError:
            log.warning(f"Could not get current rate of {coin}. Assume 0?")
            raise
            # rate_from_contract = 0

        return self._rates_converter.convert_rate_from_contract_units(
            rate_from_contract
        )

    async def _get_pair_price_future(self, coin: Coin, loop) -> PairPrice:
        return PairPrice(
            pair=(coin, self._config.market), price=await self.get_rate(coin, loop)
        )

    async def _get_previous_rates(self, loop) -> Dict[Tuple[Coin, Coin], float]:
        previous_rate_futures = [
            asyncio.ensure_future(self._get_pair_price_future(coin, loop))
            for coin in self._config.coins
        ]
        previous_rates = await asyncio.gather(*previous_rate_futures, loop=loop)

        return {pair_price.pair: pair_price.price for pair_price in previous_rates}

    def _prepare_rates_for_update(
        self, previous_rates: Dict[Tuple[Coin, Coin], float], new_rates: List[PairPrice]
    ) -> List[PairPrice]:
        updates = []
        for pair_price in new_rates:
            if pair_price.price and self._should_update_price(
                coin=pair_price.pair[0],
                market=pair_price.pair[1],
                previous_rate=self._get_previous_rate(
                    coin=pair_price.pair[0],
                    market=pair_price.pair[1],
                    rates=previous_rates,
                ),
                current_rate=pair_price.price,
            ):
                updates.append(pair_price)

        return updates

    @staticmethod
    def _should_update_price(
        coin: Coin,
        market: Coin,
        previous_rate: Optional[float],
        current_rate: Optional[float],
    ) -> bool:
        if previous_rate == 0:
            log.info(
                f"{coin.symbol} has no previous rate stored. Updating to "
                + f"current rate."
            )
            current_change = 1.0
            should_update = True
        else:
            current_change = abs(current_rate - previous_rate) / previous_rate
            should_update = current_change > coin.volatility

        log.info(
            f'{coin.symbol + "/" + market.symbol + ":":10} '
            + f"previous={previous_rate:<10.7f} "
            + f"current={current_rate:<10.7f} "
            + f"change={current_change:<10.7f} "
            + f"threshold={coin.volatility:<10.7f} update={should_update}"
        )
        return should_update

    @staticmethod
    def _get_previous_rate(
        coin: Coin, market: Coin, rates: Dict[Tuple[Coin, Coin], float]
    ) -> Optional[float]:
        try:
            return rates[(coin, market)]
        except KeyError:
            return None


# TODO: test this class
class ContractRateArgumentsConverter:
    CHANGE_FACTOR = 10 ** 18

    def __init__(self, market: Coin) -> None:
        self._market = market

    @staticmethod
    def format_coin_prices_for_setter(coin_price_data: List[PairPrice]) -> List:
        sources = []
        rates = []

        for pair_price in coin_price_data:
            # TODO: should this code receive a None? Saw while running.
            if pair_price.price:
                sources.append(pair_price.pair[0].address)
                rates.append(
                    ContractRateArgumentsConverter.convert_price_to_contract_units(
                        pair_price.price
                    )
                )

        return [sources, rates]

    @staticmethod
    def format_coin_for_getter(coin: Coin) -> List[str]:
        return [coin.address]

    @staticmethod
    def convert_rate_from_contract_units(rate_from_contract: float) -> float:
        return rate_from_contract / ContractRateArgumentsConverter.CHANGE_FACTOR

    @staticmethod
    def convert_price_to_contract_units(price: float) -> float:
        """ Prices in the contract have some limitations.

        Prices are kept as a uint in the contract so we shift the decimal point a couple of places.
        e.g. A rate of OMG/ETH: 0.016883 means that one OMG costs 0.016883 ETH, and so the contract will be sent a rate
        of 16,883,000,000,000,000.
        """
        return round(price * ContractRateArgumentsConverter.CHANGE_FACTOR)
