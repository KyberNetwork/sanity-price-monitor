""" Initialized the sanity rates in all of the coins.

Helps during development when the coin addresses change or a new coin is added.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import fire

project_base_path = Path(__file__).resolve().parent.parent
sys.path.append(project_base_path.as_posix())

from pricemonitor.coin_volatility import CoinVolatilityFile
from pricemonitor.config import Config
from pricemonitor.storing.storing import SanityContractUpdater
from pricemonitor.storing.web3_connector import Web3Connector

log = logging.getLogger(__name__)

CONFIG_FILE_PATH_KOVAN = '../smart-contracts/deployment_kovan.json'
COIN_VOLATILITY_PATH = '../coin_volatility.json'


def prepare_rates(config):
    return [
        ((coin, config.market), 1)
        for coin in config.coins
    ]


async def main(loop, configuration_file_path=CONFIG_FILE_PATH_KOVAN, coin_volatility_path=COIN_VOLATILITY_PATH):
    config = Config(configuration_file_path=configuration_file_path,
                    coin_volatility=CoinVolatilityFile(coin_volatility_path))
    contract_updater = SanityContractUpdater(Web3Connector(private_key=config.private_key,
                                                           contract_abi=config.get_smart_contract_abi(),
                                                           contract_address=config.get_smart_contract_address()),
                                             config=config)

    await contract_updater.update_prices(coin_price_data=prepare_rates(config), force=True, loop=loop)


def run_on_loop():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    log.debug('Starting event loop')
    loop = asyncio.get_event_loop()
    # TODO: ccxt raises exceptions when the code runs from inside a try-finally for some reason:
    # https://github.com/ccxt/ccxt/issues/345
    # try:
    #     loop.run_until_complete(main(loop))
    # finally:
    #     log.info('Closing event loop')
    #     loop.close()
    loop.run_until_complete(main(loop))


if __name__ == '__main__':
    fire.Fire(run_on_loop)
