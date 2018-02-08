# TODO: use correct chain in etherscan
import asyncio
import logging
from functools import partial

from pricemonitor.exceptions import PriceMonitorException

ETHERSCAN_PREFIX = "https://kovan.etherscan.io/tx/"

log = logging.getLogger(__name__)

NUMBER_OF_ATTEMPTS_ON_FAILURE = 10


class Web3Connector:
    def __init__(self, web3_interface, private_key, contract_abi, contract_address):
        self._web3_interface = web3_interface
        self._private_key = private_key
        self._contract_abi = contract_abi
        self._contract_address = contract_address

    async def call_local_function(self, function_name, args, loop):
        for attempt in range(NUMBER_OF_ATTEMPTS_ON_FAILURE):
            try:
                rs = await self._wrap_sync_function(call_function=self._web3_interface.call_const_function,
                                                    function_name=function_name,
                                                    args=args,
                                                    loop=loop)
                break
            except Web3ConnectionError:
                self._web3_interface.use_next_node()
        else:
            log.warning('Tried multiple times to access Ethereum nodes. Giving up.')
            return None

        log.debug(f"{function_name}({args})\n\t-> {rs}")
        return rs

    async def call_remote_function(self, function_name, args, loop):
        for attempt in range(NUMBER_OF_ATTEMPTS_ON_FAILURE):
            try:
                rs = await self._wrap_sync_function(call_function=self._web3_interface.call_function,
                                                    function_name=function_name,
                                                    args=args,
                                                    loop=loop)
                break
            except Web3ConnectionError:
                self._web3_interface.use_next_node()
            except PreviousTransactionPendingError:
                log.warning('Previous transaction failed, sleeping for 10 seconds.')
                log.warning('TODO: increase gas_price and try again using the same nonce.')
                # TODO: increase gas_price and try again using same nonce.
                asyncio.sleep(10)
        else:
            log.warning('Tried multiple times to access Ethereum nodes. Giving up.')
            return None

        log.info(f"{function_name}({args})\n\t-> {rs} ({self._web3_interface.prepare_etherscan_url(rs)})")
        return rs

    async def _wrap_sync_function(self, call_function, function_name, args, loop):
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
        except ValueError as e:
            log.exception(e)
            raise PreviousTransactionPendingError() from e


class PreviousTransactionPendingError(RuntimeError, PriceMonitorException):
    pass


class Web3ConnectionError(RuntimeError):
    def __init__(self, msg, call_function, function_name, args):
        super().__init__(f"{msg} (call_function={call_function.__name__}, function_name={function_name}, args={args})")
