""" This module allows for creating instances of the OptionQuoteProcessor class. """

from .internal.input_checking import check_create_q_proc_args
from .globals import *
from .internal.option_quote_processor import InternalQuoteProcessor
from .internal.quote_surface_construction import get_quote_surface
from .internal.curve_construction import InternalRateCurve, InternalForwardCurve


def create_q_proc(forwards: np.ndarray,
                  rates: np.ndarray,
                  option_prices: np.ndarray,
                  price_unit: PriceUnit,
                  expiries: np.ndarray,
                  strikes: np.ndarray,
                  strike_unit: StrikeUnit = StrikeUnit.strike,
                  liquidity_proxies: Optional[np.ndarray] = None) -> OptionQuoteProcessor:
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

    quote_surface = get_quote_surface(forwards=forwards,
                                      rates=rates,
                                      option_prices=option_prices,
                                      price_unit=price_unit,
                                      expiries=expiries,
                                      strikes=strikes,
                                      strike_unit=strike_unit,
                                      liquidity_proxies=liquidity_proxies)

    return InternalQuoteProcessor(quote_surface=quote_surface)


def create_rate_curve(times: np.ndarray,
                      zero_rates: np.ndarray) -> RateCurve:
    """ Returns a rate curve that inter- and extrapolates given zero rates.

    :param times:
    :param zero_rates: continuously compounded zero rates.
    :return:
    """

    return InternalRateCurve(times=times, zero_rates=zero_rates)


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
