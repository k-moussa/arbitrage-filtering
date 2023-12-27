""" This module allows for computing the call value for strike zero. """

import numpy as np


def compute_zero_strike_call_value(discount_factor: float,
                                   forward: float) -> float:

    return discount_factor * forward
