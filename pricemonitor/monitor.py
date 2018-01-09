import asyncio
import json
import logging

from pricemonitor.monitoring.exchangeprices import ExchangePriceMonitor

CONFIGURATION_FILE_PATH = '../smart-contracts/deployment_dev.json'

MARKET = 'ETH'

MONITOR_INTERVAL_IN_MILLISECONDS = 5_000

async def main(loop):
    config = load_config()

    market = MARKET
    coins = [
        coin
        for coin in config['tokens']
        if coin != MARKET
    ]

    monitor = ExchangePriceMonitor(coins, market)
    await monitor.monitor(price_update_handler=print_prices, interval_in_milliseconds=MONITOR_INTERVAL_IN_MILLISECONDS,
                          loop=loop)


def print_prices(prices):
    printable_prices = [
        f"{pair}: {price:10.5}"
        for pair, price in prices
    ]
    print('\t'.join(printable_prices))


def load_config():
    with open(CONFIGURATION_FILE_PATH) as config_file:
        return json.load(config_file)


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
