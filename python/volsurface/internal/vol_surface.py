""" This module implements the VolSurface class. """

import numpy as np
from typing import Optional, List, final
from numcomp import InterpolationType, Interpolator, create_interpolator, ExtrapolationType
from qproc import ScalarOrArray, PriceUnit, StrikeUnit, OptionQuoteProcessor, FilterType, EXPIRY_KEY, STRIKE_KEY, \
    MID_KEY
from ..globals import VolSurface
from .functional_interpolator import FunctionalInterpolator, FuncInterType

SMILE_STRIKE_UNIT: final = StrikeUnit.log_moneyness
SMILE_PRICE_UNIT: final = PriceUnit.vol
EXPIRY_PRICE_UNIT: final = PriceUnit.total_var


class InterpolationData:
    def __init__(self,
                 expiry: float,
                 x: np.ndarray,
                 y: np.ndarray):
        """

        :param expiry:
        :param x: independent variables.
        :param y: dependent variables.
        """

        self.expiry: float = expiry
        self.x: np.ndarray = x
        self.y: np.ndarray = y


class VolSmile:
    def __init__(self,
                 data: InterpolationData,
                 inter_type: InterpolationType,
                 extra_type: ExtrapolationType):

        self._expiry: float = data.expiry
        self._interpolator: Interpolator = create_interpolator(x=data.x, y=data.y,
                                                               inter_type=inter_type, extra_type=extra_type)

    def __call__(self, trans_strikes: ScalarOrArray) -> ScalarOrArray:
        """ Returns the total variance(s) for the given transformed strikes.

        :param trans_strikes: strikes in the units of the interpolation data.
        :return:
        """

        vol = self._interpolator(trans_strikes)
        total_variance = vol ** 2 * self._expiry
        return total_variance


class InternalVolSurface(VolSurface):
    def __init__(self,
                 smile_inter_type: InterpolationType,
                 oqp: OptionQuoteProcessor,
                 filter_type: Optional[FilterType],
                 filter_smoothness_param: float):

        self._smile_inter_type: InterpolationType = smile_inter_type

        self._oqp: OptionQuoteProcessor = oqp
        self._filtering = filter_type is not None
        if self._filtering:
            self._oqp.filter(filter_type=filter_type, smoothing_param=filter_smoothness_param)

        self._vol_surface: FunctionalInterpolator = None

    def calibrate(self):
        """ Calibrates the volatility surface object to the given option price data.

        :return:
        """

        data = self._get_interpolation_data()
        expiries = []
        smiles = []
        for d in data:
            expiries.append(d.expiry)
            smiles.append(VolSmile(data=d, inter_type=self._smile_inter_type, extra_type=ExtrapolationType.flat))

        self._vol_surface = FunctionalInterpolator(independent_variables=np.array(expiries), funcs=smiles,
                                                   f_inter_type=FuncInterType.linear)

    def _get_interpolation_data(self) -> List[InterpolationData]:
        quotes = self._oqp.get_quotes(strike_unit=SMILE_STRIKE_UNIT, price_unit=SMILE_PRICE_UNIT)
        expiries = quotes[EXPIRY_KEY].unique()
        data = []
        for i in range(expiries.size):
            expiry = expiries[i]
            quotes_for_expiry = quotes.loc[quotes[EXPIRY_KEY] == expiry]
            strikes = quotes_for_expiry[STRIKE_KEY].values
            mid_prices = quotes_for_expiry[MID_KEY].values
            data.append(InterpolationData(expiry=expiry, x=strikes, y=mid_prices))

        return data

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

        if not self._is_calibrated():
            raise RuntimeError("calibrate() must be called before this function.")

        trans_strikes = self._oqp.transform_strike(expiry=expiry, strike=strike, input_strike_unit=strike_unit,
                                                   output_strike_unit=SMILE_STRIKE_UNIT)
        prices = self._vol_surface(x=trans_strikes, y=expiry)
        trans_prices = self._oqp.transform_price(strike=trans_strikes, strike_unit=SMILE_STRIKE_UNIT, price=prices,
                                                 input_price_unit=EXPIRY_PRICE_UNIT, output_price_unit=price_unit,
                                                 expiry=expiry)
        return trans_prices

    def _is_calibrated(self) -> bool:
        return self._vol_surface is not None