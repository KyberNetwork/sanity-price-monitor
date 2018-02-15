# TODO: use correct chain in etherscan
import logging
from functools import partial

from pricemonitor.exceptions import PriceMonitorException

NUMBER_OF_ATTEMPTS_ON_FAILURE = 10

log = logging.getLogger(__name__)


class Web3Connector:
    def __init__(self, web3_interface, private_key, contract_abi, contract_address):
        self._web3_interface = web3_interface
        self._private_key = private_key
        self._contract_abi = contract_abi
        self._contract_address = contract_address

    async def call_local_function(self, function_name, eth_args, loop):
        for attempt in range(NUMBER_OF_ATTEMPTS_ON_FAILURE):
            try:
                rs = await self._wrap_sync_function(call_function=self._web3_interface.call_const_function,
                                                    function_name=function_name,
                                                    eth_args=eth_args,
                                                    loop=loop)
                break
            except Web3ConnectionError:
                self._web3_interface.use_next_node()
        else:
            log.warning('Tried multiple times to access Ethereum nodes. Giving up.')
            return None

        log.debug(f"{function_name}({eth_args})\n\t-> {rs}")
        return rs

    async def call_remote_function(self, function_name, eth_args, loop):
        use_increased_gas_price = False
        for attempt in range(NUMBER_OF_ATTEMPTS_ON_FAILURE):
            try:
                rs = await self._wrap_sync_function(call_function=self._web3_interface.call_function,
                                                    function_name=function_name,
                                                    eth_args=eth_args,
                                                    loop=loop,
                                                    use_increased_gas_price=use_increased_gas_price)
                break
            except Web3ConnectionError:
                self._web3_interface.use_next_node()
            except PreviousTransactionPending:
                use_increased_gas_price = True
                log.debug('Previous transaction failed - pending tx with same nonce, sending with higher gas price')
            except NonceAlreadySpent:
                use_increased_gas_price = False
                log.debug('Previous transaction failed - nonce used for committed tx, sending again')
        else:
            log.warning('Tried multiple times to access Ethereum nodes. Giving up.')
            return None

        log.info(f"{function_name}({eth_args})\n\t-> {rs} ({self._web3_interface.prepare_etherscan_url(rs)})")
        return rs

    async def _wrap_sync_function(self, call_function, function_name, eth_args, loop, *args, **kwargs):
        log.debug(
            f"{call_function.__name__} calls {call_function}: eth_args:{eth_args}, args: {args}, kwargs: {kwargs}")
        web3call = partial(call_function, priv_key=self._private_key, value=0, contract_hash=self._contract_address,
                           contract_abi=self._contract_abi, function_name=function_name, eth_args=eth_args, *args,
                           **kwargs)

        try:
            rs = await loop.run_in_executor(executor=None, func=web3call)
            return rs
        except IOError as e:
            msg = "Error accessing Ethereum node"
            log.exception(msg)
            raise Web3ConnectionError(msg, call_function, function_name, eth_args) from e
        except ValueError as e:
            log.debug(f'Got ValueError: {e}')
            error_message = e.args[0]['error']['message']
            if error_message.startswith('Transaction gas price is too low'):
                # {'jsonrpc': '2.0', 'error': {'code': -32010, 'message': 'Transaction gas price is too low. There is another transaction with same nonce in the queue. Try increasing the gas price or incrementing the nonce.'}, 'id': 1}
                raise PreviousTransactionPending() from e
            elif error_message.startswith('Transaction nonce is too low'):
                # {'jsonrpc': '2.0', 'error': {'code': -32010, 'message': 'Transaction nonce is too low. Try incrementing the nonce.'}, 'id': 1}
                raise NonceAlreadySpent() from e
            else:
                raise


class PreviousTransactionPending(RuntimeError, PriceMonitorException):
    pass


class NonceAlreadySpent(RuntimeError, PriceMonitorException):
    pass


class Web3ConnectionError(RuntimeError):
    def __init__(self, msg, call_function, function_name, eth_args):
        super().__init__(
            f"{msg} (call_function={call_function.__name__}, function_name={function_name}, args={eth_args})")
