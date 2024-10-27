""" This module implements the VolSurface class. """

import numpy as np
import computils as nc
from typing import Optional, List, Tuple, final
from computils import InterpolationType, Interpolator, create_interpolator, ExtrapolationType
from qproc import ScalarOrArray, PriceUnit, StrikeUnit, OptionQuoteProcessor, FilterType, EXPIRY_KEY, STRIKE_KEY, \
    MID_KEY
from ..globals import VolSurface
from .functional_interpolator import FunctionalInterpolator, FuncInterType

SMILE_STRIKE_UNIT: final = StrikeUnit.log_moneyness
SMILE_PRICE_UNIT: final = PriceUnit.vol
EXPIRY_PRICE_UNIT: final = PriceUnit.total_var
ABS_LOG_MONEYNESS_EXTRA_POINT: final = 3.0


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
                 filter_smoothness_param: float,
                 extrapolation_param: Optional[float]):

        self._smile_inter_type: InterpolationType = smile_inter_type
        self._extrapolation_param: Optional[float] = extrapolation_param

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
            strikes, prices = self._get_augmented_quotes(strikes=quotes_for_expiry[STRIKE_KEY].values,
                                                         prices=quotes_for_expiry[MID_KEY].values, expiry=expiry)
            data.append(InterpolationData(expiry=expiry, x=strikes, y=prices))

        return data

    def _get_augmented_quotes(self,
                              strikes: np.ndarray,
                              prices: np.ndarray,
                              expiry: float) -> Tuple[np.ndarray, np.ndarray]:

        augmented_strikes = strikes
        augmented_prices = prices
        if self._extrapolation_param is not None:
            if strikes[-1] < ABS_LOG_MONEYNESS_EXTRA_POINT:
                extra_vol_rhs = self._get_extrapolated_value(log_moneyness=ABS_LOG_MONEYNESS_EXTRA_POINT, expiry=expiry,
                                                             base_vol=augmented_prices[-1])
                augmented_prices = np.append(augmented_prices, values=extra_vol_rhs)
                augmented_strikes = np.append(augmented_strikes, values=ABS_LOG_MONEYNESS_EXTRA_POINT)
            if strikes[0] > -ABS_LOG_MONEYNESS_EXTRA_POINT:
                extra_vol_lhs = self._get_extrapolated_value(log_moneyness=-ABS_LOG_MONEYNESS_EXTRA_POINT,
                                                             expiry=expiry, base_vol=augmented_prices[0])
                augmented_prices = np.insert(augmented_prices, obj=0, values=extra_vol_lhs)
                augmented_strikes = np.insert(augmented_strikes, obj=0, values=-ABS_LOG_MONEYNESS_EXTRA_POINT)

        return augmented_strikes, augmented_prices

    def _get_extrapolated_value(self,
                                log_moneyness: float,
                                expiry: float,
                                base_vol: float):

        ub = self._oqp.compute_upper_bound(expiry=expiry, strike=log_moneyness, strike_unit=SMILE_STRIKE_UNIT,
                                           price_unit=SMILE_PRICE_UNIT)
        lb = self._oqp.compute_lower_bound(expiry=expiry, strike=log_moneyness, strike_unit=SMILE_STRIKE_UNIT,
                                           price_unit=SMILE_PRICE_UNIT)
        lb = max(lb, base_vol)
        if lb > ub:
            extrapolated_vol = ub
        else:
            extrapolated_vol = lb + self._extrapolation_param * (ub - lb)

        return extrapolated_vol

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

    def compute_risk_neutral_density(self,
                                     expiry: float,
                                     x: ScalarOrArray) -> ScalarOrArray:

        if not self._is_calibrated():
            raise RuntimeError("calibrate() must be called before this function.")

        func = lambda z: self._compute_undiscounted_call_price(strike=z, expiry=expiry)
        density_values = nc.compute_derivative(func=func, x=x, order=2)
        return density_values

    def compute_risk_neutral_cdf(self,
                                 expiry: float,
                                 x: ScalarOrArray) -> ScalarOrArray:

        if not self._is_calibrated():
            raise RuntimeError("calibrate() must be called before this function.")

        func = lambda z: self._compute_undiscounted_call_price(strike=z, expiry=expiry)
        fo_derivatives = nc.compute_derivative(func=func, x=x, order=1)
        cdf_values = 1.0 + fo_derivatives
        return cdf_values

    def _compute_undiscounted_call_price(self,
                                         strike: ScalarOrArray,
                                         expiry: float) -> ScalarOrArray:

        log_moneyness = self._oqp.transform_strike(expiry=expiry, strike=strike, input_strike_unit=StrikeUnit.strike,
                                                   output_strike_unit=StrikeUnit.log_moneyness)
        vol = self._vol_surface(x=log_moneyness, y=expiry)
        undiscounted_call_price = self._oqp.transform_price(
            strike=strike, strike_unit=StrikeUnit.strike, price=vol, input_price_unit=PriceUnit.vol,
            output_price_unit=PriceUnit.undiscounted_call, expiry=expiry)
        return undiscounted_call_price
