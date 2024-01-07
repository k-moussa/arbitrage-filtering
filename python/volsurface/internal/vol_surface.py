""" This module implements the VolSurface class. """

import numpy as np
from typing import Optional
from numcomp import InterpolationType, Interpolator, create_interpolator, ExtrapolationType
from qproc import ScalarOrArray, PriceUnit, StrikeUnit, OptionQuoteProcessor, FilterType
from ..globals import VolSurface


class InterpolationData:
    def __init__(self,
                 expiry: float,
                 independent_variables: np.ndarray,
                 dependent_variables: np.ndarray):

        self.expiry: float = expiry
        self.independent_variables: np.ndarray = independent_variables
        self.dependent_variables: np.ndarray = dependent_variables


class VolSmile:
    def __init__(self,
                 data: InterpolationData,
                 oqp: OptionQuoteProcessor,
                 smile_price_unit: PriceUnit,
                 expiry_price_unit: PriceUnit,
                 inter_type: InterpolationType,
                 extra_type: ExtrapolationType):

        self._interpolator: Interpolator = create_interpolator(x=data.independent_variables, y=data.dependent_variables,
                                                               inter_type=inter_type, extra_type=extra_type)
        self._oqp: OptionQuoteProcessor = oqp
        self._smile_price_unit: PriceUnit = smile_price_unit
        self._expiry_price_unit: PriceUnit = expiry_price_unit

    def __call__(self, strikes: ScalarOrArray) -> ScalarOrArray:
        pass  # todo


class InternalVolSurface(VolSurface):
    def __init__(self,
                 oqp: OptionQuoteProcessor,
                 strike_inter_type: InterpolationType,
                 filter_type: Optional[FilterType]):

        self._oqp: OptionQuoteProcessor = oqp
        self._strike_inter_type: InterpolationType = strike_inter_type
        self._filter_type: Optional[FilterType] = filter_type
        self._smile_price_unit: PriceUnit = PriceUnit.vol
        self._expiry_price_unit: PriceUnit = PriceUnit.total_var

    def calibrate(self):
        """ Calibrates the volatility surface object to the given option price data.

        :return:
        """

        pass  # todo

    def get_price(self,
                  price_unit: PriceUnit,
                  expiry: float,
                  strike: ScalarOrArray,
                  strike_unit: StrikeUnit = StrikeUnit.strike) -> ScalarOrArray:
        """ Returns the option price for given expiry and strike(s) in the requested unit.

        :param price_unit:
        :param expiry:
        :param strike: scalar or (n,) array of strikes.
        :param strike_unit: optional, if None the strike unit of the
        :return: prices: an object with prices for each given strike that is of the same type and dimension as strike.
        """

        pass  # todo
