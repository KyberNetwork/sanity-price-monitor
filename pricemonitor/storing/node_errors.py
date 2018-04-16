"""Detect cause of errors received from Ethereum nodes.

Parity sources: https://github.com/paritytech/parity/blob/master/rpc/src/v1/helpers/errors.rs#L309
Geth sources: https://github.com/ethereum/go-ethereum/blob/master/core/tx_pool.go#L45

Examples of JSON responses received from Parity:
{'jsonrpc': '2.0',
 'error': {'code': -32010,
           'message': 'Transaction gas price is too low.
                       There is another transaction with same nonce in the queue.
                       Try increasing the gas price or incrementing the nonce.'
          },
 'id': 1}

{'jsonrpc': '2.0',
 'error': {'code': -32010,
           'message': 'Transaction nonce is too low. Try incrementing the nonce.'
          },
 'id': 1}
"""
from pricemonitor.exceptions import PriceMonitorException


def detect_replacing_tx_low_gas_price(message):
    """Detect error that returns when trying to replace a tx by using same nonce, but not increasing gas price.
    """
    return _detect_replacing_tx_low_gas_price_parity(message) or _detect_replacing_tx_low_gas_price_geth(message)


def detect_nonce_too_low(message):
    """Detect error that returns when trying to use a nonce that has already been committed.
    """
    return _detect_nonce_too_low_parity(message) or _detect_nonce_too_low_geth(message)


def _detect_replacing_tx_low_gas_price_parity(message):
    """source:
    https://github.com/paritytech/parity/blob/1cd93e4cebeeb7b14e02b4e82bc0d4f73ed713d9/rpc/src/v1/helpers/errors.rs#L316
    """
    return message.startswith('Transaction gas price is too low')


def _detect_replacing_tx_low_gas_price_geth(message):
    """source:
    https://github.com/ethereum/go-ethereum/blob/60516c83b011998e20d52e2ff23b5c89527faf83/core/tx_pool.go#L59
    """
    return message.startswith('replacement transaction underpriced')


def _detect_nonce_too_low_parity(message):
    """source:
    https://github.com/paritytech/parity/blob/1cd93e4cebeeb7b14e02b4e82bc0d4f73ed713d9/rpc/src/v1/helpers/errors.rs#L314
    """
    return message.startswith('Transaction nonce is too low')


def _detect_nonce_too_low_geth(message):
    """source:
    https://github.com/ethereum/go-ethereum/blob/60516c83b011998e20d52e2ff23b5c89527faf83/core/tx_pool.go#L51
    """
    return message.startswith('nonce too low')


class PreviousTransactionPending(Exception, PriceMonitorException):
    pass


class NonceAlreadySpent(Exception, PriceMonitorException):
    pass
