import logging
from functools import partial

from pricemonitor.storing import web3_interface as web3

# TODO: use correct chain in etherscan
ETHERSCAN_PREFIX = f"https://kovan.etherscan.io/tx/"


class Web3Connector(object):
    def __init__(self, private_key, contract_abi, contract_address):
        self._private_key = private_key
        self._contract_abi = contract_abi
        self._contract_address = contract_address
        self._log = logging.getLogger(self.__class__.__name__)

    async def call_local_function(self):
        pass

    async def call_network_function(self, function_name, args, loop):
        web3call = partial(web3.call_function,
                           priv_key=self._private_key,
                           value=0,
                           contract_hash=self._contract_address,
                           contract_abi=self._contract_abi,
                           function_name=function_name,
                           args=args)
        rs = await loop.run_in_executor(executor=None, func=web3call)
        transaction_url = f"{function_name}({args})\n\t-> {rs} ({ETHERSCAN_PREFIX}{rs})"
        self._log.info(transaction_url)
        print(transaction_url)
        return rs
