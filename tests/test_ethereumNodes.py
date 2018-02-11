import logging

from pricemonitor.storing.ethereum_nodes import EthereumNetwork

logging.disable(logging.WARNING)


def test__current_node__returns_node():
    nodes = EthereumNetwork(["a"], '')

    assert nodes.current_node() == "a"


def test__current_node__returns_node_when_asking_multiple_times():
    nodes = EthereumNetwork(["a"], '')

    assert nodes.current_node() == "a"
    assert nodes.current_node() == "a"


def test__next_node__returns_next_node():
    nodes = EthereumNetwork(["a", "b"], '')

    assert nodes.next_node() == "b"


def test__next_node_is_cyclic__returns_next_node():
    nodes = EthereumNetwork(["a", "b"], '')

    assert nodes.next_node() == "b"
    assert nodes.next_node() == "a"


def test__etherscan__returns_etherscan_url():
    nodes = EthereumNetwork(["a"], 'http://etherscan.io/')

    assert nodes.etherscan('0x111') is not None


def test__etherscan__returns_unique_etherscan_url_per_tx():
    nodes = EthereumNetwork(["a"], 'http://etherscan.io/')

    a = nodes.etherscan('0x111')
    b = nodes.etherscan('0x111')
    c = nodes.etherscan('0x222')

    assert a == b
    assert a != c
