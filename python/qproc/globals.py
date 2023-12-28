""" This module collects all exposed types from the qproc package. """

import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from typing import final, Optional, Tuple

CALENDAR_DAYS_YEAR: final = 365
EXPIRY_KEY: final = 'expiry'
STRIKE_KEY: final = 'strike'
MID_KEY: final = 'mid'
BID_KEY: final = 'bid'
ASK_KEY: final = 'ask'
LIQ_KEY: final = 'liq'

DEFAULT_SMOOTHING_PARAM: final = 0.0
DEFAULT_SMOOTHING_PARAM_GRID: final = (0.1, 0.2, 0.3, 0.4, 0.5)


class SurfacePlotType(Enum):
    separate = 0
    combined_2d = 1


class PriceUnit(Enum):
    vol = 0
    call = 1
    normalized_call = 2
    total_var = 3


class StrikeUnit(Enum):
    strike = 0
    moneyness = 1  # forward moneyness
    log_moneyness = 2


class Side(Enum):
    mid = 0
    bid = 1
    ask = 2


class FilterType(Enum):
    discard = 0
    strike = 1
    expiry_forward = 2


class OptionQuoteProcessor(ABC):

    @abstractmethod
    def filter(self,
               filter_type: FilterType,
               smoothing_param: Optional[float] = DEFAULT_SMOOTHING_PARAM,
               param_grid: Tuple[float] = DEFAULT_SMOOTHING_PARAM_GRID):
        """ Filters the quotes based on the chosen filtering type.

        :param filter_type:
        :param smoothing_param:
        :param param_grid: smoothing parameters to optimize over.
        :return:
        """

    @abstractmethod
    def get_quotes(self,
                   strike_unit: StrikeUnit,
                   price_unit: PriceUnit) -> pd.DataFrame:
        """ Returns the quotes sorted in ascending order by expiry (first) and strike (second).

        :param strike_unit:
        :param price_unit:
        :return:
        """
