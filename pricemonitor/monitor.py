import asyncio
import logging
import os
from collections import namedtuple
from enum import Enum
from functools import partial

import fire

from pricemonitor.coin_volatility import CoinVolatilityFile
from pricemonitor.config import Config
from pricemonitor.datasource.exchanges import Exchange
from pricemonitor.monitoring.exchange_prices import ExchangePriceMonitor
from pricemonitor.monitoring.monitor_actions import (
    PrintValuesMonitor,
    PrintValuesAndAverageMonitor,
    ContractUpdaterMonitor,
    ContractUpdaterMonitorForce)

Task = namedtuple('TASK', 'exchange_data_action, monitor_action, interval_in_millis')

CONFIG_FILE_PATH_DEV = 'smart-contracts/deployment_dev.json'
CONFIG_FILE_PATH_KOVAN = 'smart-contracts/deployment_kovan.json'

COIN_VOLATILITY_PATH = 'coin_volatility.json'


class Tasks(Enum):
    PRINT_AVERAGE_LAST_MINUTE = Task(
        exchange_data_action=Exchange.get_last_minute_trades_average_or_last_trade,
        monitor_action=PrintValuesMonitor,
        interval_in_millis=5 * 1_000)

    VOLATILITY_EVERY_THIRTY_SECONDS = Task(
        exchange_data_action=partial(Exchange.get_volatility, time_period=4),
        monitor_action=PrintValuesAndAverageMonitor,
        interval_in_millis=30 * 1_000)

    UPDATE_CONTRACT_AVERAGE_LAST_MINUTE = Task(
        exchange_data_action=Exchange.get_last_minute_trades_average_or_last_trade,
        monitor_action=ContractUpdaterMonitor,
        interval_in_millis=1 * 60 * 1_000)

    UPDATE_CONTRACT_AVERAGE_LAST_SECOND_FORCE = Task(
        exchange_data_action=Exchange.get_last_minute_trades_average_or_last_trade,
        monitor_action=ContractUpdaterMonitorForce,
        interval_in_millis=1 * 1_000)


async def main(task, loop, configuration_file_path=CONFIG_FILE_PATH_KOVAN, coin_volatility_path=COIN_VOLATILITY_PATH,
               private_key=None):
    config = Config(configuration_file_path=configuration_file_path,
                    coin_volatility=CoinVolatilityFile(coin_volatility_path),
                    private_key=private_key)
    monitor = ExchangePriceMonitor(config.coins, config.market)
    await monitor.monitor(monitor_action=task.value.monitor_action(config),
                          interval_in_milliseconds=task.value.interval_in_millis,
                          loop=loop,
                          exchange_data_action=task.value.exchange_data_action)


def run_on_loop(task_name='UPDATE_CONTRACT_AVERAGE_LAST_MINUTE', private_key=None):
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
    logging.getLogger('asyncio').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    log = logging.getLogger(__name__)
    log.debug('Starting event loop')
    loop = asyncio.get_event_loop()
    # TODO: ccxt raises exceptions when the code runs from inside a try-finally for some reason:
    # https://github.com/ccxt/ccxt/issues/345
    # try:
    #     loop.run_until_complete(main(loop))
    # finally:
    #     log.info('Closing event loop')
    #     loop.close()
    loop.run_until_complete(main(task=Tasks[task_name], loop=loop, private_key=private_key))


if __name__ == '__main__':
    fire.Fire(run_on_loop)
