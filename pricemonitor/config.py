import json

CONFIGURATION_FILE_PATH = '../smart-contracts/deployment_dev.json'


class Config:
    MARKET = 'ETH'

    def __init__(self):
        self._config = self._load_config()
        self.market = Config.MARKET
        self.coins = [
            coin
            for coin in self._config['tokens']
            if coin != Config.MARKET
        ]

    @staticmethod
    def _load_config():
        with open(CONFIGURATION_FILE_PATH) as config_file:
            return json.load(config_file)
