""" This module implements the rate and forward curves. """

import numpy as np
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


class InternalForwardCurve(ForwardCurve):
    def __init__(self,
                 spot: float,
                 times: np.ndarray,
                 forwards: np.ndarray):

        self._spot: float = spot
        self._times: np.ndarray = times
        log_depo_diff = np.log(forwards/spot)
        self._interpolator: Interpolator = create_interpolator(x=times, y=log_depo_diff,
                                                               inter_type=InterpolationType.linear,
                                                               extra_type=ExtrapolationType.nan)  # todo: extrapolation

    def get_forward(self, time: float) -> float:
        log_depo_diff = self._interpolator(time)
        forward = self._spot * np.exp(log_depo_diff)
        return forward

    def spot(self) -> float:
        return self._spot
