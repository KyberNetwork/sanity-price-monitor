import pytest


def _get_target_class():
    from pricemonitor.storing.storing import ContractRateArgumentsConverter
    return ContractRateArgumentsConverter


def _make_one(*args, **kwargs):
    return _get_target_class()(*args, **kwargs)


@pytest.mark.skip
def test_initial():
    formatter = _make_one()

    assert formatter is not None


def test_format_coin_prices_for_setter():
    pass
