from collections import defaultdict

from util.calculations import calculate_average
from util.time import prepare_time_str


class MonitorAction:
    def act(self, data):
        raise NotImplementedError


class PrintValuesMonitor(MonitorAction):
    def act(self, data):
        self._print(data)

    @staticmethod
    def _print(data):
        printable_prices = [
            f'{pair}: {price:10.5}'
            for pair, price in data
        ]
        prices_str = '\t'.join(printable_prices)
        print(f'{prepare_time_str()} {prices_str}')


class PrintValuesAndAverageMonitor(PrintValuesMonitor):
    def __init__(self):
        self._all_data = defaultdict(lambda: [])

    def act(self, data):
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
            self._all_data[pair].append(price)
