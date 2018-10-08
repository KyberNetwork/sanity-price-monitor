import asyncio
from datetime import datetime
import json
import logging.config
import os
import shutil
from collections import namedtuple
from pprint import pprint
from typing import Iterable

import fire

from util import network
from util.network import DataFormat
from util.string_utils import _prepare_title, _is_yes

DEFAULT_VOLATILITY = 0.05
BACKUP_SUFFIX = "%b-%d-%y-%H:%M:%S"

Diff = namedtuple('Diff', ['added', 'removed'])


async def _get_current_tokens(coin_volatility_file):
    with open(coin_volatility_file) as f:
        data = json.load(f)

    coins = data['markets']['ETH'].keys()
    return coins


async def _get_new_tokens(url):
    data = await network.get_response_content_from_get_request(
        url, format=DataFormat.TEXT)
    d = json.loads(data)
    filtered = {
        token
        for token, params in d['tokens'].items()
        if params['internal use']
    }
    return filtered


def calculate_diff(current_tokens: Iterable[str],
                   new_tokens: Iterable[str]
                   ) -> Diff:
    return Diff(added=set(new_tokens) - set(current_tokens),
                removed=set(current_tokens) - set(new_tokens))


def print_diff(diff):
    print(_prepare_title('added:'))
    for t in diff.added:
        print(t)
    print()

    print(_prepare_title('removed:'))
    for t in diff.removed:
        print(t)


def _create_backup(filepath):
    modified_time = os.path.getmtime(filepath)
    timestamp = datetime.fromtimestamp(modified_time).strftime(BACKUP_SUFFIX)
    shutil.copyfile(filepath, f'{filepath}_{timestamp}')


def _update_coin_volatility_file(coin_volatility_file, token_diff):
    with open(coin_volatility_file) as f:
        data = json.load(f)

    for coin in token_diff.removed:
        del data['markets']['ETH'][coin]

    for coin in token_diff.added:
        data['markets']['ETH'][coin] = DEFAULT_VOLATILITY

    # print('Output:\n', json.dumps(data, indent=2))
    try:
        _create_backup(coin_volatility_file)
        with open(coin_volatility_file, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        print(f'{coin_volatility_file} updated successfully.')

    except IOError:
        log.exception('Error updating file')


async def main(coin_volatility_file, new_json_url):
    current = await _get_current_tokens(coin_volatility_file)
    new = await _get_new_tokens(new_json_url)
    token_diff = calculate_diff(current, new)
    print_diff(token_diff)
    should_update = input('\nWant to update current coin_volatility.json '
                          'file? ')

    if _is_yes(should_update):
        _update_coin_volatility_file(coin_volatility_file, token_diff)


def run_on_loop(coin_volatility_file, new_json_url):
    log.debug('Starting event loop')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(coin_volatility_file, new_json_url))


def _setup_logging(name):
    def _set_external_modules_logging():
        logging.getLogger('asyncio').setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.INFO)
        logging.getLogger('ccxt').setLevel(logging.INFO)

    global log
    # logging.config.fileConfig('logging.conf')
    # logging.config.fileConfig('logging_local.conf')
    _set_external_modules_logging()
    log = logging.getLogger(name)
    return log


if __name__ == '__main__':
    log = _setup_logging('json_changes')

    fire.Fire(run_on_loop)
