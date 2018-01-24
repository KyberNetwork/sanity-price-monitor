# Volatility Calculator

Extract data that was archived by [collector](https://github.com/KyberNetwork/reserve-collector) and extract the 
volatility levels per coin per exchange.

Volatility is defined by `(max(prices) - min(prices)) / max(prices)`.

This summary is based on single data point calculated for hourly trades data, taken in 4 minute intervals.

# Usage
```bash
$ python3 calculate_from_collector.py
```