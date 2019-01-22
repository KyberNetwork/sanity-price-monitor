from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List

from pricemonitor.config import Config
from pricemonitor.producing.data_producer import PairPrice
from pricemonitor.storing.storing import SanityContractUpdater
from pricemonitor.storing.web3_connector import Web3Connector
from pricemonitor.storing.web3_interface import Web3Interface
from util.calculations import calculate_average
from util.time import prepare_time_str


class DataConsumer(ABC):
    def __init__(self, config: Config) -> None:
        self._config = config

    @abstractmethod
    async def act(self, data: List[PairPrice], loop) -> None:
        pass


class PrintValues(DataConsumer):
    async def act(self, data: List[PairPrice], loop) -> None:
        self._print(data)

    @staticmethod
    def _print(data: List[PairPrice]) -> None:
        printable_prices = [
            f"{pair_price.pair[0].symbol}/{pair_price.pair[1].symbol}: {pair_price.price:10.5}"
            for pair_price in data
            if pair_price.price is not None
        ]
        prices_str = "\t".join(printable_prices)
        print(f"{prepare_time_str()} {prices_str}")


class PrintValuesAndAverage(PrintValues):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self._all_data = defaultdict(list)  # type: defaultdict

    async def act(self, data: List[PairPrice], loop) -> None:
        self._print(data)
        self._save_data(data)
        self._print_averages()

    def _print_averages(self) -> None:
        printable_averages = [
            f"{pair}: {calculate_average(price_list)}"
            for pair, price_list in self._all_data.items()
        ]
        averages = "\t".join(printable_averages)
        print(f"Average:\n {averages}\n")

    def _save_data(self, data: List[PairPrice]) -> None:
        for pair_price in data:
            if pair_price.price is not None:
                self._all_data[pair_price.pair].append(pair_price.price)


class ContractUpdater(DataConsumer):
    def __init__(self, config: Config, force=False) -> None:
        super().__init__(config)
        self._print_monitor = PrintValues(config)
        self._updater = SanityContractUpdater(
            Web3Connector(
                private_key=config.private_key,
                contract_abi=config.get_smart_contract_abi(),
                contract_address=config.contract_address,
                web3_interface=Web3Interface(config.network),
            ),
            config=config,
        )
        self._force = force

    async def act(self, data: List[PairPrice], loop) -> None:
        await self._print_monitor.act(data, loop)
        await self._updater.update_prices(
            coin_price_data=data, force=self._force, loop=loop
        )


class ContractUpdaterForce(ContractUpdater):
    def __init__(self, config: Config, force=True) -> None:
        super().__init__(config=config, force=force)
