import logging
import os

import pytest

from pricemonitor.config import Coin
from pricemonitor.storing.storing import SanityContractUpdater, ContractRateArgumentsConverter
from pricemonitor.storing.web3_connector import PreviousTransactionPendingError

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

SOME_TX_ADDRESS = '0x9865'

OMG = Coin(symbol='OMG', address='0x44444', name='OMG', volatility=0.05)
ETH = Coin(symbol='ETH', address='0x22222', name='ETH', volatility=0.05)

INITIAL_OMG_PRICE = 0.1

SIMILAR_TO_INITIAL_OMG_ETH_RATE = 0.103
DIFFERENT_FROM_INITIAL_OMG_ETH_RATE = 0.110
SOME_OTHER_OMG_ETH_RATE = 0.1667

SOME_OTHER_COIN_PRICES = [
    ((OMG, ETH), SOME_OTHER_OMG_ETH_RATE),
]

SIMILAR_TO_INITIAL_COIN_PRICES = [
    ((OMG, ETH), SIMILAR_TO_INITIAL_OMG_ETH_RATE),
]

DIFFERENT_FROM_INITIAL_OMG_ETH_PRICES = [
    ((OMG, ETH), DIFFERENT_FROM_INITIAL_OMG_ETH_RATE),
]


class Web3ConnectorFake:
    async def call_remote_function(self, function_name, args, loop):
        return SOME_TX_ADDRESS

    async def call_local_function(self, function_name, args, loop):
        return 0


class Web3ConnectorFakeWithInitialOMG(Web3ConnectorFake):
    INITIAL_OMG_CONTRACT_RATE = INITIAL_OMG_PRICE * 10 ** 18

    def __init__(self):
        self.prices = {OMG.address: Web3ConnectorFakeWithInitialOMG.INITIAL_OMG_CONTRACT_RATE}
        self.raise_previous_transaction_pending = False

    async def call_local_function(self, function_name, args, loop):
        if function_name == SanityContractUpdater.GET_RATE_FUNCTION_NAME:
            return [self.prices[args[0]]]

        return super().call_local_function(function_name, args, loop)

    async def call_remote_function(self, function_name, args, loop):
        if self.raise_previous_transaction_pending:
            raise PreviousTransactionPendingError()

        if function_name == SanityContractUpdater.SET_RATES_FUNCTION_NAME:
            coins, rates = args
            for coin_address, rate in zip(coins, rates):
                self.prices[coin_address] = rate
            return SOME_TX_ADDRESS

        return super().call_remote_function(function_name, args, loop)


class ConfigFake:
    def __init__(self):
        self.market = ETH
        self.coins = [OMG]


def test_initial():
    s = SanityContractUpdater(Web3ConnectorFake(), ConfigFake())

    assert s is not None


@pytest.mark.asyncio
async def test_set_rates(event_loop):
    rateConverter = ContractRateArgumentsConverter(market=ETH)
    web3_connector = Web3ConnectorFakeWithInitialOMG()
    s = SanityContractUpdater(web3_connector, ConfigFake())

    tx = await s.set_rates(SOME_OTHER_COIN_PRICES, event_loop)

    assert tx is not None
    assert rateConverter.convert_price_to_contract_units(SOME_OTHER_OMG_ETH_RATE) == web3_connector.prices[OMG.address]


@pytest.mark.asyncio
async def test_get_rate(event_loop):
    s = SanityContractUpdater(Web3ConnectorFakeWithInitialOMG(), ConfigFake())

    rs = await s.get_rate(OMG, event_loop)

    assert Web3ConnectorFakeWithInitialOMG.INITIAL_OMG_CONTRACT_RATE / 10 ** 18 == rs


@pytest.mark.asyncio
async def test_update_prices__initial(event_loop):
    converter = ContractRateArgumentsConverter(market=ETH)
    web3_connector = Web3ConnectorFakeWithInitialOMG()
    s = SanityContractUpdater(web3_connector, ConfigFake())

    rs = await s.update_prices(DIFFERENT_FROM_INITIAL_OMG_ETH_PRICES, event_loop)

    assert rs is not None


@pytest.mark.asyncio
async def test_update_prices__significant_change__rates_get_updated(event_loop):
    converter = ContractRateArgumentsConverter(market=ETH)
    web3_connector = Web3ConnectorFakeWithInitialOMG()
    s = SanityContractUpdater(web3_connector, ConfigFake())

    rs = await s.update_prices(DIFFERENT_FROM_INITIAL_OMG_ETH_PRICES, event_loop)
    omg_price_after = web3_connector.prices[OMG.address]

    assert rs is not None
    assert converter.convert_price_to_contract_units(DIFFERENT_FROM_INITIAL_OMG_ETH_RATE) == omg_price_after


@pytest.mark.asyncio
async def test_update_prices__insignificant_change__rates_do_not_change(event_loop):
    web3_connector = Web3ConnectorFakeWithInitialOMG()
    s = SanityContractUpdater(web3_connector, ConfigFake())

    omg_price_before = web3_connector.prices[OMG.address]
    rs = await s.update_prices(SIMILAR_TO_INITIAL_COIN_PRICES, event_loop)
    omg_price_after = web3_connector.prices[OMG.address]

    assert rs is None
    assert omg_price_before == omg_price_after
    # TODO: assert web3_connector.set_prices was not called!


@pytest.mark.skip
@pytest.mark.asyncio
async def test_update_prices__mixed_price_updates__only_major_changes_get_updated():
    assert False


@pytest.mark.asyncio
async def test_update_prices__two_very_fast_rates_updates__merged_update_sent_with_higher_gas_price(event_loop):
    converter = ContractRateArgumentsConverter(market=ETH)
    web3_connector = Web3ConnectorFakeWithInitialOMG()
    s = SanityContractUpdater(web3_connector, ConfigFake())

    rs = await s.update_prices(DIFFERENT_FROM_INITIAL_OMG_ETH_PRICES, event_loop)

    web3_connector.raise_previous_transaction_pending = True
    rs = await s.update_prices(SOME_OTHER_COIN_PRICES, event_loop)

    assert rs is not None
    # assert converter.convert_price_to_contract_units(DIFFERENT_FROM_INITIAL_OMG_ETH_RATE) == omg_price_after


@pytest.mark.skip
@pytest.mark.asyncio
async def test_update_prices__significant_change__node_accessed_to_verify_tx_confirmed():
    assert False


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_prices__exception_calling_node__rate_0_assumed():
    assert False


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_prices__exception_calling_node__code_does_not_crash():
    assert False

# @pytest.mark.skip
# @pytest.mark.asyncio
# async def test_get_prices__async_timeout(event_loop):
#     # timeout = 5 * 60
#     timeout = 1
#     async with async_timeout.timeout(timeout, loop=event_loop):
#         res = None
#         while not res:
#             try:
#                 res = await async_wrapper_for_slow_failing_method()
#             except Exception:
#                 pass
#
#     assert res is None
#
#
# @pytest.mark.asyncio
# async def test_timeout(event_loop):
#     res = None
#     try:
#         res = await asyncio.wait_for(slow(10), timeout=0.1, loop=event_loop)
#     except Exception:
#         pass
#
#     assert res is None
#
#
# async def slow(seconds):
#     res = None
#     for i in range(seconds):
#         res = await async_wrapper_for_slow_failing_method()
#         if res is not None:
#             break
#
#     return res
#
#
# A = 0
# async def async_wrapper_for_slow_failing_method():
#     global A
#     await asyncio.sleep(1)
#     A += 1
#     logging.error('--- A=', A)
#     return A if A > 5 else None
