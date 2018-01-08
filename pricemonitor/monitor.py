import asyncio
import logging

import yaml

from pricemonitor.monitoring.exchangeprices import ExchangePriceMonitor


async def main(loop):
    config = load_config()

    market = config['market']
    coins = config['coins']

    monitor = ExchangePriceMonitor(coins, market)
    await monitor.monitor(loop)


def load_config():
    with open('config.yaml') as config_file:
        return yaml.load(config_file, Loader=yaml.CLoader)


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
    loop.run_until_complete(main(loop))
