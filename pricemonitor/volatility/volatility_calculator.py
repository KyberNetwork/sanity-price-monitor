import pandas as pd
from pandas.tseries.offsets import DateOffset

# data = [
#     {'exchange': 'Binance', 'pair': {'base': 'LINK', 'quote': 'ETH'}, 'price': 0.0009432, 'quantity': 21,
#      'timestamp': 1516614901013, 'type': 'buy'},
#     {'exchange': 'Binance', 'pair': {'base': 'LINK', 'quote': 'ETH'}, 'price': 0.00094321, 'quantity': 1056,
#      'timestamp': 1516614901013, 'type': 'buy'},
#     {'exchange': 'Binance', 'pair': {'base': 'WTC', 'quote': 'ETH'}, 'price': 0.026671, 'quantity': 6,
#      'timestamp': 1516614902751, 'type': 'buy'},
#     {'exchange': 'Liqui', 'pair': {'base': 'salt', 'quote': 'eth'}, 'price': 0.00765445, 'quantity': 0.40312841,
#      'timestamp': 1516614903000, 'type': 'buy'},
#     {'exchange': 'Bittrex', 'pair': {'base': 'OMG', 'quote': 'ETH'}, 'price': 0.01649565,
#      'quantity': 0.55536053, 'timestamp': 1516614903000, 'type': 'buy'},
#     {'exchange': 'Binance', 'pair': {'base': 'WTC', 'quote': 'ETH'}, 'price': 0.026667, 'quantity': 4.5,
#      'timestamp': 1516614905984, 'type': 'buy'},
#     {'exchange': 'Liqui', 'pair': {'base': 'trx', 'quote': 'eth'}, 'price': 7.557e-05, 'quantity': 601.18627826,
#      'timestamp': 1516614907000, 'type': 'sell'},
#     {'exchange': 'Liqui', 'pair': {'base': 'trx', 'quote': 'eth'}, 'price': 7.558e-05, 'quantity': 132.31013496,
#      'timestamp': 1516614907000, 'type': 'sell'}]

FOUR_MINUTE_OFFSET = DateOffset(minutes=4)
HOUR_MINUTE_OFFSET = DateOffset(hours=1)


def calculate_volatility_score(data, exchange_filter=None):
    df = pd.DataFrame(data)

    if exchange_filter:
        df = df[df['exchange'] == exchange_filter]
    if df.empty:
        return None

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    start_time = df['timestamp'].iat[0]
    end_time = df['timestamp'].iat[-1]

    volatility_results = []

    slice_end = end_time
    while slice_end - HOUR_MINUTE_OFFSET >= start_time:
        data_in_slice = df[prepare_time_range(df, end_time, HOUR_MINUTE_OFFSET)]
        volatility_results.append(calculate_volatility(data_in_slice))
        slice_end -= FOUR_MINUTE_OFFSET

    return sum(volatility_results) / len(volatility_results) if len(volatility_results) != 0 else None


def prepare_time_range(df, end_time, offset):
    return (df['timestamp'] > end_time - offset) & (df['timestamp'] <= end_time)


def calculate_volatility(data_in_slice):
    max_price = max(data_in_slice['price'])
    min_price = min(data_in_slice['price'])
    return (max_price - min_price) / max_price
