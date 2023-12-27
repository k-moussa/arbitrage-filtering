""" This module allows for constructing a quote surface from input data. """

import numpy as np
from typing import Optional
from ..globals import *
from .quote_structures import QuoteSurface, QuoteSlice, Quote


def get_quote_surface(forwards: np.ndarray,
                      rates: np.ndarray,
                      option_prices: np.ndarray,
                      price_unit: PriceUnit,
                      expiries: np.ndarray,
                      strikes: np.ndarray,
                      strike_unit: StrikeUnit,
                      liquidity_proxies: Optional[np.ndarray]) -> QuoteSurface:

    quote_surface = QuoteSurface(price_unit=price_unit, strike_unit=strike_unit)
    sided_option_prices = _get_sided_prices(option_prices)
    _fill_quote_surface(sided_option_prices, strikes=strikes, expiries=expiries, forwards=forwards,
                        rates=rates, liquidity_proxies=liquidity_proxies, quote_surface=quote_surface)
    return quote_surface


def _get_sided_prices(option_prices: np.ndarray) -> np.ndarray:

    are_prices_sided = False
    are_prices_2d = len(option_prices.shape) == 2
    if are_prices_2d:
        are_prices_sided = option_prices.shape[1] == 2

    if not are_prices_sided:
        option_prices = option_prices.reshape((-1, 1))
        option_prices = np.repeat(option_prices, 2, axis=1)  # bid = ask = mid

    return option_prices


def _fill_quote_surface(sided_option_prices,
                        strikes: np.ndarray,
                        expiries: np.ndarray,
                        forwards: np.ndarray,
                        rates: np.ndarray,
                        liquidity_proxies: Optional[np.ndarray],
                        quote_surface: QuoteSurface):

    n_quotes = sided_option_prices.shape[0]

    current_expiry = -np.inf
    forward = np.nan
    quote_slice: Optional[QuoteSlice] = None
    qslice_index = -1

    for i in range(n_quotes):
        expiry = expiries[i]
        if expiry < current_expiry:
            raise RuntimeError("option_prices must be passed in ascending order w.r.t. their expiry.")

        elif expiry > current_expiry:
            qslice_index += 1
            current_expiry = expiry
            forward = forwards[qslice_index]
            quote_slice = QuoteSlice(forward=forward, rate=rates[qslice_index],
                                     expiry=expiry)

            quote_surface.add_slice(quote_slice)

        bid = sided_option_prices[i, 0]
        ask = sided_option_prices[i, 1]
        strike = strikes[i]
        liq_proxy = _get_liquidity_proxy(liquidity_proxies, index=i, strike=strike, forward=forward)
        q = Quote(bid=bid, ask=ask, strike=strike, liq_proxy=liq_proxy)
        quote_slice.add_quote(q)


def _get_liquidity_proxy(liq_proxies: Optional[np.ndarray],
                         index: int,
                         strike: float,
                         forward: float) -> float:

    if liq_proxies is None:
        return -np.abs(strike/forward - 1.0)

    return liq_proxies[index]
