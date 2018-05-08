import time


def prepare_time_str() -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())


def minutes_ago_in_millis_since_epoch(minutes: float) -> float:
    return int(round(time.time() * 1_000)) - 60_000 * minutes
