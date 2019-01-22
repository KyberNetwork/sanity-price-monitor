import asyncio

import fire

from pricemonitor.volatility.trades_from_collector_archive import (
    TradesFromCollectorArchive,
    TradesDownloader,
)
from pricemonitor.volatility.volatility_calculator import calculate_volatility_score

EXCHANGES = ["Binance", "Bittrex", "Liqui", "Bitfinex"]
COINS = {"SNT", "OMG", "EOS", "SALT", "KNC"}
MARKET = "ETH"


def get_average_of_hourly_volatility(trades, exchange_filter=None):
    return calculate_volatility_score(trades, exchange_filter)


async def main(loop):
    get_trades = TradesFromCollectorArchive(COINS, MARKET, TradesDownloader())
    trades_per_coin = await get_trades.download_all_trade_data_per_coin()

    # sanity
    _verify_timestamp_order(trades_per_coin["EOS"])

    for coin in COINS:
        print(f"\n{coin}\n------")
        for exchange in EXCHANGES:
            average_volatility = get_average_of_hourly_volatility(
                trades_per_coin[coin], exchange_filter=exchange
            )
            print(f"{exchange}: {average_volatility}")


def _verify_timestamp_order(trades):
    previous_ts = 0
    for trade in trades:
        if trade["timestamp"] >= previous_ts:
            continue
        print("!!! Timestamp ordering error, exiting")
        import sys

        sys.exit(1)


def run_on_loop():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop))
    finally:
        loop.close()


if __name__ == "__main__":
    fire.Fire(run_on_loop)
