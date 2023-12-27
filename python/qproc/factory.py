""" This module allows for creating instances of the OptionQuoteProcessor class. """

import numpy as np
from typing import Optional
from.internal.input_checking import check_create_q_proc_args
from .globals import *
from .internal.option_quote_processor import InternalQuoteProcessor


def create_q_proc(option_prices: np.ndarray,
                  price_unit: PriceUnit,
                  strikes: np.ndarray,
                  expiries: np.ndarray,
                  forwards: np.ndarray,
                  rates: np.ndarray,
                  liquidity_proxies: Optional[np.ndarray] = None,
                  filter_type: FilterType = FilterType.na) -> OptionQuoteProcessor:
    """ Creates an instance of OptionQuoteProcessor.

    :param option_prices: (n,2) array with bid and ask prices or an (n,) array with mid prices. The option prices must
        be in ascending order w.r.t. to their expiry.
    :param price_unit: unit in which the option prices are expressed.
    :param strikes: (n,) array with strikes corresponding to the option prices.
    :param expiries: (n,) array with expiries for each option corresponding to the option prices.
    :param forwards: (n_expiries,) array with forwards for every expiry date.
    :param rates: (n_expiries,) array with zero rates (= continuously-compounded yields) for every expiry date.
    :param liquidity_proxies: (n,) array with liquidity proxies (e.g., trading volume), used by the arbitrage filter.
        By default, -|(K - F)/F| is used, with strike K and forward F.
    :param filter_type:
    :return:
    """

    check_create_q_proc_args(option_prices=option_prices,
                             price_unit=price_unit,
                             strikes=strikes,
                             expiries=expiries,
                             forwards=forwards,
                             rates=rates,
                             liquidity_proxies=liquidity_proxies,
                             filter_type=filter_type)

    return InternalQuoteProcessor(option_prices=option_prices,
                                  price_unit=price_unit,
                                  strikes=strikes,
                                  expiries=expiries,
                                  forwards=forwards,
                                  rates=rates,
                                  liquidity_proxies=liquidity_proxies,
                                  filter_type=filter_type)
