""" This module allows for creating instances of the OptionQuoteProcessor class. """

import numpy as np
from typing import Union
from .internal.input_checking import check_create_q_proc_args
from .globals import *
from .internal.option_quote_processor import InternalQuoteProcessor
from .internal.quote_surface_construction import get_quote_surface
from .internal.curve_construction import InternalRateCurve, InternalForwardCurve
from .internal.liquidity_proxy_computation import compute_moneyness_based_liquidity_proxies
from .internal.quote_transformation import transform_strike


def create_q_proc(forwards: Union[np.ndarray, ForwardCurve],
                  rates: Union[np.ndarray, RateCurve],
                  option_prices: np.ndarray,
                  price_unit: PriceUnit,
                  expiries: np.ndarray,
                  strikes: np.ndarray,
                  strike_unit: StrikeUnit = StrikeUnit.strike,
                  liquidity_proxies: Optional[np.ndarray] = None,
                  spot: float = np.nan) -> OptionQuoteProcessor:
    """ Creates an instance of OptionQuoteProcessor.

    :param forwards: (n_expiries,) array with forwards for every expiry date, or a forward curve object.
    :param rates: (n_expiries,) array with zero rates (= continuously-compounded yields) for every expiry date, or a
        rate curve object.
    :param option_prices: (n,2) array with bid and ask prices or an (n,) array with mid prices. The option prices must
        be in ascending order w.r.t. to their expiry.
    :param price_unit: unit in which the option prices are expressed.
    :param expiries: (n,) array with expiries for each option corresponding to the option prices.
    :param strikes: (n,) array with strikes corresponding to the option prices.
    :param strike_unit:
    :param liquidity_proxies: (n,) array with liquidity proxies (e.g., trading volume), used by the arbitrage filter.
        By default, -|(K - F)/F| is used, with strike K and forward F.
    :param spot: the spot price; only needed if forwards is not a curve object.
    :return:
    """

    check_create_q_proc_args(forwards=forwards,
                             rates=rates,
                             option_prices=option_prices,
                             price_unit=price_unit,
                             expiries=expiries,
                             strikes=strikes,
                             strike_unit=strike_unit,
                             liquidity_proxies=liquidity_proxies)

    if isinstance(forwards, np.ndarray) or isinstance(rates, np.ndarray):
        unique_expiries = np.sort(np.unique(expiries))
        if isinstance(forwards, np.ndarray):
            forwards = create_forward_curve(spot=spot, times=unique_expiries, forwards=forwards)
        if isinstance(rates, np.ndarray):
            rates = create_rate_curve(times=unique_expiries, zero_rates=rates)

    if liquidity_proxies is None:
        forwards_for_strikes = forwards.get_forward(expiries)
        actual_strikes = transform_strike(strike=strikes, input_strike_unit=strike_unit,
                                          output_strike_unit=StrikeUnit.strike, forward=forwards_for_strikes)
        liquidity_proxies = compute_moneyness_based_liquidity_proxies(strikes=actual_strikes, expiries=expiries,
                                                                      forward_curve=forwards)

    quote_surface = get_quote_surface(option_prices=option_prices,
                                      price_unit=price_unit,
                                      expiries=expiries,
                                      strikes=strikes,
                                      strike_unit=strike_unit,
                                      liquidity_proxies=liquidity_proxies)

    return InternalQuoteProcessor(quote_surface=quote_surface,
                                  forward_curve=forwards,
                                  rate_curve=rates)


def create_forward_curve(spot: float,
                         times: np.ndarray,
                         forwards: np.ndarray) -> ForwardCurve:
    """ Returns a forward curve that inter- and extrapolates given forwards.

    :param spot:
    :param times:
    :param forwards:
    :return:
    """

    return InternalForwardCurve(spot=spot, times=times, forwards=forwards)


def create_rate_curve(times: np.ndarray,
                      zero_rates: np.ndarray) -> RateCurve:
    """ Returns a rate curve that inter- and extrapolates given zero rates.

    :param times:
    :param zero_rates: continuously compounded zero rates.
    :return:
    """

    return InternalRateCurve(times=times, zero_rates=zero_rates)
