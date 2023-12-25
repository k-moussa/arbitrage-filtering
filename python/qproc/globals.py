""" This module collects all exposed types from the qproc package. """

import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
from typing import final

DAYS_IN_YEAR: final = 365
EXPIRY_INDEX: final = 0
STRIKE_INDEX: final = 1
MID_INDEX: final = 2
BID_INDEX: final = 3
ASK_INDEX: final = 4
LIQ_INDEX: final = 5


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
    def get_quote_matrix(self,
                         strike_trans: StrikeTransform,
                         price_unit: PriceUnit) -> np.ndarray:
        """ Returns an (n_quotes, n_features) matrix of quotes in ascending order first by expiry and then by strike.

        :param strike_trans:
        :param price_unit:
        :return:
        """
