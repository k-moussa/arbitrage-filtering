""" This module collects all exposed types from the qproc package. """

import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from typing import final, Optional, Tuple
from numcomp import ScalarOrArray

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
    undiscounted_call = 2
    normalized_call = 3
    total_var = 4


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


class RateCurve(ABC):
    @abstractmethod
    def get_zero_rate(self, time: ScalarOrArray) -> ScalarOrArray:
        """ Computes the zero rate for given time (in years).

        :param time:
        :return:
        """

    @abstractmethod
    def get_discount_factor(self, time: ScalarOrArray) -> ScalarOrArray:
        """ Computes the discount factor for given time (in years).

        :param time:
        :return:
        """


class ForwardCurve(ABC):
    @abstractmethod
    def get_forward(self, time: ScalarOrArray) -> ScalarOrArray:
        """ Computes the forward price for given time (in years).

        :param time:
        :return:
        """

    @abstractmethod
    def spot(self) -> float:
        """ Returns the spot price."""


class OptionQuoteProcessor(ABC):

    @abstractmethod
    def transform_strike(self,
                         expiry: float,
                         strike: ScalarOrArray,
                         input_strike_unit: StrikeUnit,
                         output_strike_unit: StrikeUnit) -> ScalarOrArray:
        """ Transforms the given strike(s) to the desired strike unit.

        :param expiry
        :param strike:
        :param input_strike_unit:
        :param output_strike_unit
        :return: transformed strike(s), of the same type and shape as strike.
        """

    @abstractmethod
    def transform_price(self,
                        strike: ScalarOrArray,
                        strike_unit: StrikeUnit,
                        price: ScalarOrArray,
                        input_price_unit: PriceUnit,
                        output_price_unit: PriceUnit,
                        expiry: float) -> ScalarOrArray:
        """ Transforms the given price(s) to the desired price unit.

        :param strike:
        :param strike_unit
        :param price:
        :param input_price_unit:
        :param output_price_unit:
        :param expiry:
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
        
    @abstractmethod
    def compute_lower_bound(self,
                            expiry: float,
                            strike: ScalarOrArray,
                            strike_unit: StrikeUnit,
                            price_unit: PriceUnit) -> ScalarOrArray:
        """ Computes the lower bound for given expiry and strike implied by the quotes. The bounds are expressed in the
            chosen price unit. 
            
            Remark: this function can be used only after a call to 'filter' (i.e., once the quotes have been filtered). 
        
        :param expiry: 
        :param strike: 
        :param strike_unit: 
        :param price_unit: 
        :return: 
        """

    @abstractmethod
    def compute_upper_bound(self,
                            expiry: float,
                            strike: ScalarOrArray,
                            strike_unit: StrikeUnit,
                            price_unit: PriceUnit) -> ScalarOrArray:
        """ Computes the upper bound for given expiry and strike implied by the quotes. The bounds are expressed in the
            chosen price unit. 

            Remark: this function can be used only after a call to 'filter' (i.e., once the quotes have been filtered). 

        :param expiry: 
        :param strike: 
        :param strike_unit: 
        :param price_unit: 
        :return: 
        """
