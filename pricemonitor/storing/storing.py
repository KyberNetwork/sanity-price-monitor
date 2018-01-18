import logging

from pycoin.serialize import h2b

from pricemonitor.storing.web3_connector import Web3Connector


class SanityContractUpdater:
    # TODO: get actual contract from submodule
    CONTRACT_ABI_PATH = 'storing/contract.abi'
    # TODO: get from actual contract
    SANITY_ADDRESS = '5735d385811e423D0E33a93861E687AEb590a00A'

    UPDATE_PRICES_FUNCTION_NAME = 'setSanityRates'

    def __init__(self, config):
        self._price_formatter = ContractPriceFormatter()
        self._web3 = Web3Connector(private_key=(h2b(config.get_admin_private())),
                                   contract_abi=self._obtain_contract_abi(SanityContractUpdater.CONTRACT_ABI_PATH),
                                   contract_address=SanityContractUpdater.SANITY_ADDRESS)
        self._log = logging.getLogger(self.__class__.__name__)

    async def update_prices(self, coin_price_data, loop):
        rs = await self._web3.call_network_function(
            function_name=SanityContractUpdater.UPDATE_PRICES_FUNCTION_NAME,
            args=(self._price_formatter.format_coin_prices_for_setter(coin_price_data)),
            loop=loop)
        return rs

    @staticmethod
    def _obtain_contract_abi(contract_abi_path):
        with open(contract_abi_path) as contract_abi_file:
            return contract_abi_file.read()


class ContractPriceFormatter:
    @staticmethod
    def format_coin_prices_for_setter(coin_price_data):
        sources = []
        rates = []

        for (coin, market), price in coin_price_data:
            # TODO: should this code receive a None? Saw while running.
            if price:
                sources.append(coin.address)
                rates.append(ContractPriceFormatter._convert_price_to_contract_units(price))

        return [sources, rates]

    @staticmethod
    def _convert_price_to_contract_units(price):
        """ Prices in the contract have some limitations.

        Prices are kept as a uint in the contract so we shift the decimal point a couple of places.
        e.g. A rate of OMG/ETH: 0.016883 means that one OMG costs 0.016883 ETH, and so the contract will be sent a rate
        of 16,883,000,000,000,000.
        """
        return round(price * 10 ** 18)
