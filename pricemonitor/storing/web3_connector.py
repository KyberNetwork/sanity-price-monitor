import logging
from functools import partial

from pricemonitor.storing import web3_interface as web3

# TODO: use correct chain in etherscan
ETHERSCAN_PREFIX = f"https://kovan.etherscan.io/tx/"

log = logging.getLogger(__name__)


class Web3Connector(object):
    def __init__(self, private_key, contract_abi, contract_address):
        self._private_key = private_key
        self._contract_abi = contract_abi
        self._contract_address = contract_address

    async def call_local_function(self, function_name, args, loop):
        rs = await self.wrap_sync_function(
            call_function=web3.call_const_function, function_name=function_name, args=args, loop=loop)

        transaction_url = f"{function_name}({args})\n\t-> {rs}"
        # TODO: fix logging problem
        log.info(transaction_url)
        print(transaction_url)
        return rs

    async def call_remote_function(self, function_name, args, loop):
        rs = await self.wrap_sync_function(
            call_function=web3.call_function, function_name=function_name, args=args, loop=loop)

        transaction_url = f"{function_name}({args})\n\t-> {rs} ({ETHERSCAN_PREFIX}{rs})"
        # TODO: fix logging problem
        log.info(transaction_url)
        print(transaction_url)
        return rs

    async def wrap_sync_function(self, call_function, function_name, args, loop):
        web3call = partial(call_function,
                           priv_key=self._private_key,
                           value=0,
                           contract_hash=self._contract_address,
                           contract_abi=self._contract_abi,
                           function_name=function_name,
                           args=args)
        try:
            rs = await loop.run_in_executor(executor=None, func=web3call)
            return rs
        except IOError as e:
            msg = "Error accessing Ethereum node"
            log.exception(msg)
            raise Web3ConnectionError(msg, call_function, function_name, args) from e


class Web3ConnectionError(RuntimeError):
    def __init__(self, msg, call_function, function_name, args):
        super().__init__(f"{msg} (call_function={call_function.__name__}, function_name={function_name}, args={args})")
