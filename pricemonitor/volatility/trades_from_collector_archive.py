import asyncio
import itertools
import json
import re

from util import network
from util.network import DataFormat


class TradesDownloader:
    TRADE_FILE_PATTERN = re.compile(r'<a href="(\w+)"')
    TRADE_ARCHIVE_BASE_URL = 'http://52.77.19.90:3000/archive/'

    async def download_all_trades(self):
        print('Downloading trades data from collector archive')
        trade_urls = await self._get_trade_urls()

        # TODO: remove:
        # print('!!! limiting the data to 5 files')
        # trade_urls = trade_urls[:5]

        data_fetching_tasks = [
            self._read_data_from_web_file(trade_url)
            for trade_url in trade_urls
        ]
        trades_in_files = await asyncio.gather(*data_fetching_tasks)

        print(f'Downloaded all trades - total of {len(trades_in_files)} files')
        return trades_in_files

    async def _get_trade_urls(self):
        data = await network.get_response_content_from_get_request(url=TradesDownloader.TRADE_ARCHIVE_BASE_URL,
                                                                   format=DataFormat.TEXT)

        trade_urls = [
            self._prepare_trades_url_from_line(line)
            for line in data.splitlines()
            if 'href="trade_' in line
        ]

        print(f'Found {len(trade_urls)} URLs')
        return trade_urls

    async def _read_data_from_web_file(self, trades_url):
        print(f'Downloading data from {trades_url} - start')
        data = await network.get_response_content_from_get_request(url=trades_url, format=DataFormat.TEXT, timeout=240)

        trades = [
            normalize_trade_values(json.loads(line))
            for line in data.splitlines()
        ]

        print(f'Downloading data from {trades_url} - finished with {len(trades)} trades')
        return trades

    def _prepare_trades_url_from_line(self, line):
        match = TradesDownloader.TRADE_FILE_PATTERN.search(line)
        filename = match.group(1)
        return f'{TradesDownloader.TRADE_ARCHIVE_BASE_URL}{filename}'


class TradesFromCollectorArchive:
    def __init__(self, coins, market, trades_downloader):
        self._downloader = trades_downloader
        self._coins = coins
        self._market = market

    async def download_all_trade_data_per_coin(self):
        trades_in_files = await self._downloader.download_all_trades()

        trades_per_coin = {
            coin: []
            for coin in self._coins
        }

        for trade in itertools.chain(*trades_in_files):
            coin = trade['pair']['base']
            if coin in self._coins:
                trades_per_coin[coin].append(trade)

        print('\nSummary:\n----------')
        for coin, trades in trades_per_coin.items():
            print(f'{coin}: Found {len(trades)} trades')

        return trades_per_coin


def normalize_trade_values(trade):
    return {
        "exchange": trade["exchange"],
        "pair": convert_values_to_uppercase(trade["pair"]),
        "price": trade["price"],
        "quantity": trade["quantity"],
        "timestamp": trade["timestamp"],
        "type": trade["type"]
    }


def convert_values_to_uppercase(original_dict):
    return {
        key: value.upper()
        for key, value in original_dict.items()
    }
