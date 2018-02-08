import itertools
from enum import Enum


class EthereumNetwork:
    def __init__(self, nodes, etherscan_prefix):
        self._nodes = itertools.cycle(nodes)
        self._current_node = next(self._nodes)
        self._etherscan_prefix = etherscan_prefix

    def current_node(self):
        return self._current_node

    def next_node(self):
        self._current_node = next(self._nodes)
        return self._current_node

    def etherscan(self, tx):
        return self._etherscan_prefix + tx


class Network(Enum):
    MAINNET = EthereumNetwork(nodes=['https://mainnet.infura.io',
                                     'https://api.mycryptoapi.com/eth',
                                     'https://api.myetherapi.com/eth',
                                     'https://mew.giveth.io/'],
                              etherscan_prefix='https://etherscan.io/tx/')

    KOVAN = EthereumNetwork(nodes=['https://kovan.infura.io'],
                            etherscan_prefix='https://kovan.etherscan.io/tx/')
