""" This module collects all exposed types from the qproc package. """

import numpy as np
import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from typing import final, Optional, Tuple, Union

CALENDAR_DAYS_YEAR: final = 365
EXPIRY_KEY: final = 'expiry'
STRIKE_KEY: final = 'strike'
MID_KEY: final = 'mid'
BID_KEY: final = 'bid'
ASK_KEY: final = 'ask'
LIQ_KEY: final = 'liq'

DEFAULT_SMOOTHING_PARAM: final = 0.0
DEFAULT_SMOOTHING_PARAM_GRID: final = (0.1, 0.2, 0.3, 0.4, 0.5)

Scalar: final = Union[int, float]
ScalarOrArray: final = Union[Scalar, np.ndarray]


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

    @staticmethod
    def get_transformed_strike(strike: ScalarOrArray,
                               strike_unit: StrikeUnit,
                               forward: float) -> ScalarOrArray:
        """ Transforms the given strike(s) to the desired strike unit.

        :param strike:
        :param strike_unit:
        :param forward:
        :return: transformed strike(s), of the same type and shape as strike.
        """

    @staticmethod
    def get_price(strike: ScalarOrArray,
                  price: ScalarOrArray,
                  price_unit: PriceUnit,
                  target_price_unit: PriceUnit,
                  expiry: float,
                  discount_factor: float,
                  forward: float) -> ScalarOrArray:
        """ Transforms the given price(s) to the desired price unit.

        :param strike:
        :param price:
        :param price_unit:
        :param target_price_unit:
        :param expiry:
        :param discount_factor:
        :param forward:
        :return: transformed price(s), of the same type and shape as strike.
        """

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
