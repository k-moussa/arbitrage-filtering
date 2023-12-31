""" This module allows for computing default liquidity proxies. """

import numpy as np
from ..globals import ForwardCurve


def compute_moneyness_based_liquidity_proxies(strikes: np.ndarray,
                                              expiries: np.ndarray,
                                              forward_curve: ForwardCurve) -> np.ndarray:

    forwards = forward_curve.get_forward(expiries)
    moneyness_based_liquidity_proxies = 1.0 / (1.0 + np.abs(strikes - forwards))
    return moneyness_based_liquidity_proxies
