from abc import ABC, abstractmethod
from collections import namedtuple
from typing import List

from pricemonitor.config import Coin

PairPrice = namedtuple('PairPrice', ['pair', 'price'])


class DataProducer(ABC):
    def __init__(self, coins: List[Coin], market: Coin) -> None:
        self._coins = coins
        self._market = market

    @abstractmethod
    async def get_data(self, loop) -> List[PairPrice]:
        pass
