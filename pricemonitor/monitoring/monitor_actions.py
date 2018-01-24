from collections import defaultdict

from pricemonitor.storing.storing import SanityContractUpdater
from pricemonitor.storing.web3_connector import Web3Connector
from util.calculations import calculate_average
from util.time import prepare_time_str


class MonitorAction:
    def __init__(self, config):
        self._config = config

    async def act(self, data, loop):
        raise NotImplementedError


class PrintValuesMonitor(MonitorAction):
    async def act(self, data, loop):
        self._print(data)

    @staticmethod
    def _print(data):
        printable_prices = [
            f'{coin.symbol}/{market.symbol}: {price:10.5}'
            for (coin, market), price in data
            if price is not None
        ]
        prices_str = '\t'.join(printable_prices)
        print(f'{prepare_time_str()} {prices_str}')


class PrintValuesAndAverageMonitor(PrintValuesMonitor):
    def __init__(self, config):
        super().__init__(config)
        self._all_data = defaultdict(lambda: [])

    async def act(self, data, loop):
        self._print(data)
        self._save_data(data)
        self._print_averages()

    def _print_averages(self):
        printable_averages = [
            f'{pair}: {calculate_average(price_list)}'
            for pair, price_list in self._all_data.items()
        ]
        averages = '\t'.join(printable_averages)
        print(f'Average:\n {averages}\n')

    def _save_data(self, data):
        for pair, price in data:
            if price is not None:
                self._all_data[pair].append(price)


class ContractUpdaterMonitor(MonitorAction):
    def __init__(self, config):
        super().__init__(config)
        self._print_monitor = PrintValuesMonitor(config)
        self._updater = SanityContractUpdater(Web3Connector(private_key=config.get_admin_private_in_bytes(),
                                                            contract_abi=config.get_smart_contract_abi(),
                                                            contract_address=config.get_smart_contract_address()))

    async def act(self, data, loop):
        await self._print_monitor.act(data, loop)
        await self._updater.update_prices(coin_price_data=data, loop=loop)
