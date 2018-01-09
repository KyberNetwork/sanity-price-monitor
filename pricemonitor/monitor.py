import asyncio
import logging
from collections import namedtuple
from enum import Enum

from pricemonitor.config import Config
from pricemonitor.datasource.exchanges import Exchange
from pricemonitor.monitoring.exchange_prices import ExchangePriceMonitor
from pricemonitor.monitoring.monitor_actions import PrintValuesMonitor, PrintValuesAndAverageMonitor

Task = namedtuple('TASK', 'exchange_data_action, monitor_action, interval_in_millis')


class Tasks(Enum):
    AVERAGE_LAST_MINUTE = Task(
        exchange_data_action=Exchange.get_last_minute_trades_average_or_last_trade,
        monitor_action=PrintValuesMonitor,
        interval_in_millis=5_000)

    VOLATILITY_EVERY_TWO_MINUTES = Task(
        exchange_data_action=Exchange.get_volatility,
        monitor_action=PrintValuesAndAverageMonitor,
        interval_in_millis=(2 * 60 * 1_000))


async def main(task, loop):
    config = Config()
    monitor = ExchangePriceMonitor(config.coins, config.market)
    await monitor.monitor(
        monitor_action=task.value.monitor_action(),
        interval_in_milliseconds=task.value.interval_in_millis,
        loop=loop,
        exchange_data_action=task.value.exchange_data_action)


if __name__ == '__main__':
    log = logging.getLogger('main')
    log.debug('Starting event loop')
    loop = asyncio.get_event_loop()
    # TODO: ccxt raises exceptions when the code runs from inside a try-finally for some reason - https://github.com/ccxt/ccxt/issues/345
    # try:
    #     loop.run_until_complete(main(loop))
    # finally:
    #     log.info('Closing event loop')
    #     loop.close()
    # loop.run_until_complete(main(Tasks.AVERAGE_LAST_MINUTE, loop))
    loop.run_until_complete(main(Tasks.VOLATILITY_EVERY_TWO_MINUTES, loop))
