import logging
import logging.config


def setup_logging():
    global log
    logging.config.fileConfig('logging.conf')
    _set_external_modules_logging()
    log = logging.getLogger(__name__)


def _set_external_modules_logging():
    logging.getLogger('asyncio').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.INFO)
