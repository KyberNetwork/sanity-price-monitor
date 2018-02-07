import json
import logging
import time

import requests
import rlp
from ethereum import utils, transactions
from ethereum.abi import ContractTranslator
from pycoin.serialize import b2h, h2b

log = logging.getLogger(__name__)


class Web3Interface:
    def __init__(self, network):
        self._network = network

    def call_function(self, priv_key, value, contract_hash, contract_abi, function_name, args):
        translator = ContractTranslator(json.loads(contract_abi))
        call = translator.encode_function_call(function_name, args)
        return self._make_transaction(priv_key, contract_hash, value, call)

    def call_const_function(self, priv_key, value, contract_hash, contract_abi, function_name, args):
        # src_address = b2h(utils.privtoaddr(priv_key))
        translator = ContractTranslator(json.loads(contract_abi))
        call = translator.encode_function_call(function_name, args)
        # nonce = get_num_transactions(src_address)
        # gas_price = get_gas_price_in_wei()

        # start_gas = eval_startgas(
        # src_address, contract_hash, value, b2h(call), gas_price)
        # nonce = int(nonce, 16)
        # gas_price = int(gas_price, 16)
        # start_gas = int(start_gas, 16) + 100000
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
        params = ["0x" + address, "pending"]
        nonce = self._json_call("eth_getTransactionCount", params)
        return nonce

    def _get_gas_price_in_wei(self):
        return self._json_call("eth_gasPrice", [])

    def _eval_startgas(self, src, dst, value, data, gas_price):
        params = {"value": "0x" + str(value),
                  "gasPrice": gas_price}
        if len(data) > 0:
            params["data"] = "0x" + str(data)
        if len(dst) > 0:
            params["to"] = "0x" + dst

        return self._json_call("eth_estimateGas", [params])

    # global_nonce = -1

    def _make_transaction(self, src_priv_key, dst_address, value, data):
        # global global_nonce

        src_address = b2h(utils.privtoaddr(src_priv_key))
        nonce = self._get_num_transactions(src_address)
        gas_price = self._get_gas_price_in_wei()
        data_as_string = b2h(data)
        # print len(data_as_string)
        # if len(data) > 0:
        #    data_as_string = "0x" + data_as_string
        # start_gas = eval_startgas(src_address, dst_address, value, data_as_string, gas_price)
        start_gas = "0xF4240"

        nonce = int(nonce, 16)
        # if(global_nonce < 0):
        # global_nonce = nonce

        # nonce = global_nonce
        # global_nonce += 1

        # print(nonce)

        gas_price = int(gas_price, 16)
        # int(gas_price, 16)/20
        start_gas = int(start_gas, 16) + 100000

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
