import asyncio
import logging.config
from collections import namedtuple
from enum import Enum
from functools import partial

from pricemonitor.coin_volatility import CoinVolatilityFile
from pricemonitor.config import Config
from pricemonitor.datasource.exchanges import Exchange
from pricemonitor.monitoring.exchange_prices import ExchangePriceMonitor
from pricemonitor.monitoring.monitor_actions import (
    PrintValuesMonitor,
    PrintValuesAndAverageMonitor,
    ContractUpdaterMonitor,
    ContractUpdaterMonitorForce)
from pricemonitor.storing.ethereum_nodes import Network

Task = namedtuple('TASK', 'exchange_data_action, monitor_action, interval_in_millis')

CONTRACT_CONFIG_MAINNET = 'smart-contracts/web3deployment/mainnet_production.json'
CONTRACT_CONFIG_DEFAULT = CONTRACT_CONFIG_MAINNET

COIN_VOLATILITY_PATH = 'coin_volatility.json'

log = logging.getLogger(__name__)


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


async def main(task, loop, configuration_file_path, contract_address, private_key, network,
               coin_volatility_path=COIN_VOLATILITY_PATH):
    config = Config(configuration_file_path=configuration_file_path,
                    coin_volatility=CoinVolatilityFile(coin_volatility_path),
                    network=network,
                    contract_address=contract_address,
                    private_key=private_key)
    monitor = ExchangePriceMonitor(config.coins, config.market)
    await monitor.monitor(monitor_action=task.value.monitor_action(config),
                          interval_in_milliseconds=task.value.interval_in_millis,
                          loop=loop,
                          exchange_data_action=task.value.exchange_data_action)


def run_on_loop(private_key,
                contract_address,
                network_name,
                task_name='UPDATE_CONTRACT_AVERAGE_LAST_MINUTE',
                configuration_file_path=CONTRACT_CONFIG_DEFAULT):
    log.debug('Starting event loop')
    loop = asyncio.get_event_loop()
    # TODO: ccxt raises exceptions when the code runs from inside a try-finally for some reason:
    # https://github.com/ccxt/ccxt/issues/345
    # try:
    #     loop.run_until_complete(main(loop))
    # finally:
    #     log.info('Closing event loop')
    #     loop.close()
    loop.run_until_complete(main(task=Tasks[task_name],
                                 loop=loop,
                                 network=Network[network_name].value,
                                 private_key=private_key,
                                 contract_address=contract_address,
                                 configuration_file_path=configuration_file_path))