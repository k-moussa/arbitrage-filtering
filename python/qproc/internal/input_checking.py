""" This module collects functionality for checking input arguments. """

import numpy as np
from typing import Optional
from ..globals import *


def check_create_q_proc_args(option_prices: np.ndarray,
                             price_unit: PriceUnit,
                             strikes: np.ndarray,
                             expiries: np.ndarray,
                             forwards: np.ndarray,
                             rates: np.ndarray,
                             liquidity_proxies: Optional[np.ndarray] = None,
                             filter_type: FilterType = FilterType.na):
    """ Checks the arguments passed to create_q_proc and raises a RuntimeError if the input is invalid. """

    pass  # todo: implement
