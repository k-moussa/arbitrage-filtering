

from numcomp import create_interpolator, Interpolator, InterpolationType, ExtrapolationType
from ..globals import *


class InternalRateCurve(RateCurve):
    def __init__(self,
                 times: np.ndarray,
                 zero_rates: np.ndarray):

        self._times: np.ndarray = times
        log_deposits = zero_rates * times  # perform log linear interpolation
        self._interpolator: Interpolator = create_interpolator(x=times, y=log_deposits,
                                                               inter_type=InterpolationType.linear,
                                                               extra_type=ExtrapolationType.nan)  # todo: extrapolation

    def get_zero_rate(self, time: float) -> float:
        log_depo = self._interpolator(time)
        zero_rate = log_depo / time
        return zero_rate

    def get_discount_factor(self, time: float) -> float:
        log_depo = self._interpolator(time)
        discount_factor = np.exp(-log_depo)
        return discount_factor
