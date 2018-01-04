import asyncio
import logging

import yaml

from pricemonitor.providers import CryptoCompare


class PriceMonitor:
    def __init__(self, config, provider):
        self._config = config
        self._provider = provider

    async def monitor(self, loop):
        coins = self._config['coins']
        market = self._config['market']
        print(await self._provider.get_coin_prices(coins, market))


async def main(loop):
    config = load_config()

    monitor = PriceMonitor(config, CryptoCompare())
    await monitor.monitor(loop)


def load_config():
    with open('config.yaml') as config_file:
        return yaml.load(config_file, Loader=yaml.CLoader)


if __name__ == '__main__':
    log = logging.getLogger('main')
    log.debug('Starting event loop')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
