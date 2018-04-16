import log_config

log_config.setup_logging()

import logging

import fire
import time

import pricemonitor.monitor

WAITING_TIME_IN_SECONDS_BEFORE_RESTARTING_AFTER_CRASH = 10

log = logging.getLogger(__name__)

if __name__ == '__main__':
    while True:
        try:
            fire.Fire(pricemonitor.monitor.run_on_loop)
        except Exception:
            log.exception("Crashed with this exception:")
            time.sleep(WAITING_TIME_IN_SECONDS_BEFORE_RESTARTING_AFTER_CRASH)
