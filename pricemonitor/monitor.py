import asyncio
import logging.config
import time
from asyncio import AbstractEventLoop
from collections import namedtuple
from enum import Enum
from functools import partial

from pricemonitor.coin_volatility import CoinVolatilityFile
from pricemonitor.config import Config
from pricemonitor.consuming.consumers import (
    PrintValues,
    PrintValuesAndAverage,
    ContractUpdater,
    ContractUpdaterForce,
    DataConsumer
)
from pricemonitor.producing.all_token_prices import AllTokenPrices
from pricemonitor.producing.data_producer import DataProducer
from pricemonitor.producing.exchange_prices import (
    ExchangePrices,
    calculate_seconds_left_to_sleep
)
from pricemonitor.producing.exchanges import Exchange
from pricemonitor.storing.ethereum_nodes import Network

Task = namedtuple('TASK', ('data_producer',
                           'data_producer_params',
                           'data_consumer',
                           'interval_in_millis'))

CONTRACT_CONFIG_MAINNET = 'smart-contracts/web3deployment/mainnet_production.json'
CONTRACT_CONFIG_DEFAULT = CONTRACT_CONFIG_MAINNET

COIN_VOLATILITY_PATH = 'coin_volatility.json'

log = logging.getLogger(__name__)


class Tasks(Enum):
    PRINT_AVERAGE_LAST_MINUTE = Task(
        data_producer=ExchangePrices,
        data_producer_params={'exchange_data_action': Exchange.get_last_minute_trades_average_or_last_trade},
        data_consumer=PrintValues,
        interval_in_millis=5 * 1_000)

    VOLATILITY_EVERY_THIRTY_SECONDS = Task(
        data_producer=ExchangePrices,
        data_producer_params={'exchange_data_action': partial(Exchange.get_volatility, time_period=4)},
        data_consumer=PrintValuesAndAverage,
        interval_in_millis=30 * 1_000)

    UPDATE_CONTRACT_AVERAGE_LAST_MINUTE = Task(
        data_producer=AllTokenPrices,
        data_producer_params={'exchange_data_action': Exchange.get_last_minute_trades_average_or_last_trade},
        data_consumer=ContractUpdater,
        interval_in_millis=1 * 60 * 1_000)

    UPDATE_CONTRACT_AVERAGE_LAST_SECOND_FORCE = Task(
        data_producer=AllTokenPrices,
        data_producer_params={'exchange_data_action': Exchange.get_last_minute_trades_average_or_last_trade},
        data_consumer=ContractUpdaterForce,
        interval_in_millis=1 * 1_000)


async def main(task: Tasks,
               loop: AbstractEventLoop,
               configuration_file_path: str,
               contract_address: str,
               private_key: str,
               network: Network,
               coin_volatility_path: str = COIN_VOLATILITY_PATH
               ) -> None:
    config = Config(configuration_file_path=configuration_file_path,
                    coin_volatility=CoinVolatilityFile(coin_volatility_path),
                    network=network,
                    contract_address=contract_address,
                    private_key=private_key)

    producer = task.value.data_producer(coins=config.coins, market=config.market, **task.value.data_producer_params)
    await producer.initialize()
    await monitor_forever(data_producer=producer,
                          data_consumer=task.value.data_consumer(config),
                          interval_in_milliseconds=task.value.interval_in_millis,
                          loop=loop)


async def monitor_forever(data_producer: DataProducer,
                          data_consumer: DataConsumer,
                          interval_in_milliseconds: int,
                          loop: AbstractEventLoop
                          ) -> None:
    while True:
        start_time = time.time()
        log.info('Starting new monitor cycle')

        coin_prices = await data_producer.get_data(loop=loop)
        await data_consumer.act(data=coin_prices, loop=loop)

        await asyncio.sleep(calculate_seconds_left_to_sleep(start_time, interval_in_milliseconds), loop=loop)


def run_on_loop(private_key: str,
                contract_address: str,
                network_name: str,
                task_name: str = 'UPDATE_CONTRACT_AVERAGE_LAST_MINUTE',
                configuration_file_path: str = CONTRACT_CONFIG_DEFAULT):
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
