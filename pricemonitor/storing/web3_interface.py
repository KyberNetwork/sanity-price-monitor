import json
import logging
import time

import requests
import rlp
from ethereum import utils, transactions
from ethereum.abi import ContractTranslator
from pycoin.serialize import b2h, h2b

ADDITIONAL_START_GAS_TO_BE_ON_THE_SAFE_SIDE = 50_000
INCREASED_GAS_PRICE_FACTOR = 1.1

log = logging.getLogger(__name__)


class Web3Interface:
    def __init__(self, network):
        self._network = network

    def call_function(self, priv_key, value, contract_hash, contract_abi, function_name, eth_args,
                      use_increased_gas_price=False):
        translator = ContractTranslator(json.loads(contract_abi))
        call = translator.encode_function_call(function_name, eth_args)
        return self._make_transaction(src_priv_key=priv_key, dst_address=contract_hash, value=value, data=call,
                                      use_increased_gas_price=use_increased_gas_price)

    def call_const_function(self, priv_key, value, contract_hash, contract_abi, function_name, eth_args):
        # src_address = b2h(utils.privtoaddr(priv_key))
        translator = ContractTranslator(json.loads(contract_abi))
        call = translator.encode_function_call(function_name, eth_args)
        # nonce = get_num_transactions(src_address)
        # gas_price = get_gas_price_in_wei()

        # start_gas = eval_startgas(
        # src_address, contract_hash, value, b2h(call), gas_price)
        # nonce = int(nonce, base=16)
        # gas_price = int(gas_price, base=16)
        # start_gas = int(start_gas, base=16) + 100000
        # start_gas = 7612288

        params = {
            # "from": "0x" + src_address,
            "to": "0x" + contract_hash,
            #   "gas": "0x" + "%x" % start_gas,
            #   "gasPrice": "0x" + "%x" % gas_price,
            #   "value": "0x" + str(value),
            "data": "0x" + b2h(call)
        }

        return_value = self._json_call("eth_call", [params, "latest"])
        # print return_value
        return_value = h2b(return_value[2:])  # remove 0x
        return translator.decode_function_result(function_name, return_value)

    def is_tx_confirmed(self, tx_hash):
        if str(tx_hash).startswith("0x"):
            params = str(tx_hash)
        else:
            params = "0x" + tx_hash
        result = self._json_call("eth_getTransactionReceipt", [params])
        if result is None:
            return False
        return not (result["blockHash"] is None)

    def wait_for_tx_confirmation(self, tx_hash):
        i = 0
        while not self.is_tx_confirmed(tx_hash):
            i += 1
            time.sleep(1)
            print("wait")
            if i > 100:
                return False

    def use_next_node(self):
        self._network.next_node()
        log.info(f'Switching to next ethernet node: {self._network.current_node()}')

    def prepare_etherscan_url(self, tx):
        return self._network.etherscan(tx)

    def _json_call(self, method_name, params):
        headers = {'content-type': 'application/json'}
        # Example echo method
        payload = {
            "method": method_name,
            "params": params,
            "jsonrpc": "2.0",
            "id": 1,
        }

        # logger.debug("Payload: {}".format(payload))
        r = requests.post(url=self._network.current_node(), data=json.dumps(payload), headers=headers, timeout=5)
        assert r.status_code == requests.codes.ok, 'Blockchain connection issue.'
        data = r.json()
        result = data.get('result', None)
        if not result:
            raise ValueError(data)
        else:
            return result

    def _get_num_transactions(self, address):
        params = [f"0x{address}", "pending"]
        nonce = self._json_call("eth_getTransactionCount", params)
        return nonce

    def _get_gas_price_in_wei(self):
        return self._json_call("eth_gasPrice", [])

    def _eval_startgas(self, src, dst, value, data, gas_price):
        params = {
            "value": f"0x{value}",
            "gasPrice": gas_price,
            "from": f"0x{src}",
            "to": f"0x{dst}",
        }
        if len(data) > 0:
            params["data"] = f"0x{data}"

        return self._json_call("eth_estimateGas", [params])

    def _make_transaction(self, src_priv_key, dst_address, value, data, use_increased_gas_price):
        src_address = b2h(utils.privtoaddr(src_priv_key))
        nonce_rs = self._get_num_transactions(src_address)
        nonce = int(nonce_rs, base=16)
        log.debug(f"Using nonce {nonce}.")

        gas_price_rs = self._get_gas_price_in_wei()
        gas_price = int(gas_price_rs, base=16)
        if use_increased_gas_price:
            log.debug(f"Using increased gas price.")
            gas_price = int(gas_price * INCREASED_GAS_PRICE_FACTOR)
        log.debug(f"gas price is {gas_price}")

        start_gas_rs = self._eval_startgas(src=src_address, dst=dst_address, value=value, data=b2h(data),
                                           gas_price=gas_price_rs)
        start_gas = int(start_gas_rs, base=16) + ADDITIONAL_START_GAS_TO_BE_ON_THE_SAFE_SIDE
        log.debug(f"Estimated start gas is {start_gas}")

        tx = transactions.Transaction(nonce,
                                      gas_price,
                                      start_gas,
                                      dst_address,
                                      value,
                                      data).sign(src_priv_key)

        tx_hex = b2h(rlp.encode(tx))
        tx_hash = b2h(tx.hash)

        params = ["0x" + tx_hex]
        return_value = self._json_call("eth_sendRawTransaction", params)
        if return_value == "0x0000000000000000000000000000000000000000000000000000000000000000":
            print("Transaction failed")
            return return_value

        return return_value
