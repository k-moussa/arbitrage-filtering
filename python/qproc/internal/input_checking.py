""" This module collects functionality for checking input arguments. """

import numpy as np
from ..globals import *


def check_create_q_proc_args(forwards: np.ndarray,
                             rates: np.ndarray,
                             option_prices: np.ndarray,
                             price_unit: PriceUnit,
                             expiries: np.ndarray,
                             strikes: np.ndarray,
                             strike_unit: StrikeUnit,
                             liquidity_proxies: Optional[np.ndarray]):
    """ Checks the arguments passed to create_q_proc and raises a RuntimeError if the input is invalid. """

    pass  # todo: implement
