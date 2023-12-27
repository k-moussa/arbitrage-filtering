""" This module allows for creating instances of the OptionQuoteProcessor class. """

import numpy as np
from typing import Optional
from .internal.input_checking import check_create_q_proc_args
from .globals import *
from .internal.option_quote_processor import InternalQuoteProcessor
from .internal.quote_surface_construction import get_quote_surface


def create_q_proc(forwards: np.ndarray,
                  rates: np.ndarray,
                  option_prices: np.ndarray,
                  price_unit: PriceUnit,
                  expiries: np.ndarray,
                  strikes: np.ndarray,
                  strike_unit: StrikeUnit = StrikeUnit.strike,
                  liquidity_proxies: Optional[np.ndarray] = None,
                  filter_type: FilterType = FilterType.na,
                  smoothing_param: Optional[float] = 0.0) -> OptionQuoteProcessor:
    """ Creates an instance of OptionQuoteProcessor.

    :param forwards: (n_expiries,) array with forwards for every expiry date.
    :param rates: (n_expiries,) array with zero rates (= continuously-compounded yields) for every expiry date.
    :param option_prices: (n,2) array with bid and ask prices or an (n,) array with mid prices. The option prices must
        be in ascending order w.r.t. to their expiry.
    :param price_unit: unit in which the option prices are expressed.
    :param expiries: (n,) array with expiries for each option corresponding to the option prices.
    :param strikes: (n,) array with strikes corresponding to the option prices.
    :param strike_unit:
    :param liquidity_proxies: (n,) array with liquidity proxies (e.g., trading volume), used by the arbitrage filter.
        By default, -|(K - F)/F| is used, with strike K and forward F.
    :param filter_type:
    :param smoothing_param: optional smoothing parameter used by the arbitrage filter.
    :return:
    """

    check_create_q_proc_args(forwards=forwards,
                             rates=rates,
                             option_prices=option_prices,
                             price_unit=price_unit,
                             expiries=expiries,
                             strikes=strikes,
                             strike_unit=strike_unit,
                             liquidity_proxies=liquidity_proxies,
                             filter_type=filter_type,
                             smoothing_param=smoothing_param)

    quote_surface = get_quote_surface(forwards=forwards,
                                      rates=rates,
                                      option_prices=option_prices,
                                      price_unit=price_unit,
                                      expiries=expiries,
                                      strikes=strikes,
                                      strike_unit=strike_unit,
                                      liquidity_proxies=liquidity_proxies)

    return InternalQuoteProcessor(quote_surface=quote_surface,
                                  filter_type=filter_type,
                                  smoothing_param=smoothing_param)
