import pandas as pd
from pandas.tseries.offsets import DateOffset

FOUR_MINUTE_OFFSET = DateOffset(minutes=4)
HOUR_MINUTE_OFFSET = DateOffset(hours=1)


def calculate_volatility_score(data, exchange_filter=None):
    df = pd.DataFrame(data)

    if exchange_filter:
        df = df[df["exchange"] == exchange_filter]
    if df.empty:
        return None

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    start_time = df["timestamp"].iat[0]
    end_time = df["timestamp"].iat[-1]

    volatility_results = []

    slice_end = end_time
    while slice_end - HOUR_MINUTE_OFFSET >= start_time:
        data_in_slice = df[prepare_time_range(df, end_time, HOUR_MINUTE_OFFSET)]
        volatility_results.append(calculate_volatility(data_in_slice))
        slice_end -= FOUR_MINUTE_OFFSET

    return (
        sum(volatility_results) / len(volatility_results)
        if len(volatility_results) != 0
        else None
    )


def prepare_time_range(df, end_time, offset):
    return (df["timestamp"] > end_time - offset) & (df["timestamp"] <= end_time)


def calculate_volatility(data_in_slice):
    max_price = max(data_in_slice["price"])
    min_price = min(data_in_slice["price"])
    return abs(max_price - min_price) / max_price
