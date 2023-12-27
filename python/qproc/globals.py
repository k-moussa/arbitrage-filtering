""" This module collects all exposed types from the qproc package. """

import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from typing import final

DAYS_IN_YEAR: final = 365
EXPIRY_KEY: final = 'expiry'
STRIKE_KEY: final = 'strike'
MID_KEY: final = 'mid'
BID_KEY: final = 'bid'
ASK_KEY: final = 'ask'
LIQ_KEY: final = 'liq'


class PriceUnit(Enum):
    vol = 0
    call = 1
    normalized_call = 2


class StrikeTransform(Enum):
    strike = 0
    moneyness = 1  # forward moneyness
    log_moneyness = 2


class Side(Enum):
    mid = 0
    bid = 1
    ask = 2


class FilterType(Enum):
    na = 0
    strike = 1
    expiry = 2


class OptionQuoteProcessor(ABC):

    @abstractmethod
    def get_quotes(self,
                   strike_trans: StrikeTransform,
                   price_unit: PriceUnit) -> pd.DataFrame:
        """ Returns a matrix of quotes in ascending order first by expiry and then by strike.

        :param strike_trans:
        :param price_unit:
        :return:
        """
