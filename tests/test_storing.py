# import logging
#
# logging.disable(logging.WARNING)
#
# COIN_PRICES = {
#     'OMG': 12,
# }
#
#
# class SmartContractUpdater:
#     def __init__(self):
#         self.stored_prices = None
#
#
# def _get_target_class():
#     from pricemonitor.storing.storing import SanityContractUpdater
#     return SanityContractUpdater
#
#
# def _make_one(*args, **kwargs):
#     return _get_target_class()(*args, **kwargs)
#
#
# def test_storing__initial():
#     storing = _make_one(SmartContractUpdater())
#
#     assert storing is not None
#
#
# def test_update_coin_prices():
#     updater = SmartContractUpdater()
#     storing = _make_one(updater)
#
#     storing.update_coin_prices(COIN_PRICES)
#
#     assert updater.stored_prices == COIN_PRICES
