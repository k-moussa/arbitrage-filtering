""" This module implements the InternalQuoteProcessor class. """

import numpy as np
from typing import Optional
from ..globals import *
from .quote_structures import QuoteSurface, QuoteSlice, Quote
from .quote_map import transform_quote

COL_NAMES: final = (EXPIRY_KEY, STRIKE_KEY, MID_KEY, BID_KEY, ASK_KEY, LIQ_KEY)


class InternalQuoteProcessor(OptionQuoteProcessor):
    def __init__(self,
                 option_prices: np.ndarray,
                 price_unit: PriceUnit,
                 strikes: np.ndarray,
                 expiries: np.ndarray,
                 forwards: np.ndarray,
                 rates: np.ndarray,
                 liquidity_proxies: Optional[np.ndarray],
                 filter_type: FilterType):

        if filter_type is not FilterType.na:
            raise RuntimeError("filtering not implemented yet.")

        self._quote_surface = QuoteSurface(price_unit=price_unit)
        sided_option_prices = self._get_sided_prices(option_prices)
        self._fill_quote_surface(sided_option_prices, strikes=strikes, expiries=expiries, forwards=forwards,
                                 rates=rates, liquidity_proxies=liquidity_proxies)

    @staticmethod
    def _get_sided_prices(option_prices: np.ndarray) -> np.ndarray:

        are_prices_sided = False
        are_prices_2d = len(option_prices.shape) == 2
        if are_prices_2d:
            are_prices_sided = option_prices.shape[1] == 2

        if not are_prices_sided:
            option_prices = option_prices.reshape((-1, 1))
            option_prices = np.repeat(option_prices, 2, axis=1)  # bid = ask = mid

        return option_prices

    def _fill_quote_surface(self,
                            sided_option_prices,
                            strikes: np.ndarray,
                            expiries: np.ndarray,
                            forwards: np.ndarray,
                            rates: np.ndarray,
                            liquidity_proxies: Optional[np.ndarray]):

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

                self._quote_surface.add_slice(quote_slice)

            bid = sided_option_prices[i, 0]
            ask = sided_option_prices[i, 1]
            strike = strikes[i]
            liq_proxy = self._get_liquidity_proxy(liquidity_proxies, index=i, strike=strike, forward=forward)
            q = Quote(bid=bid, ask=ask, strike=strike, liq_proxy=liq_proxy)
            quote_slice.add_quote(q)

    @staticmethod
    def _get_liquidity_proxy(liq_proxies: Optional[np.ndarray],
                             index: int,
                             strike: float,
                             forward: float) -> float:

        if liq_proxies is None:
            return -np.abs(strike/forward - 1.0)

        return liq_proxies[index]

    def get_quotes(self,
                   strike_trans: StrikeTransform,
                   price_unit: PriceUnit) -> pd.DataFrame:

        current_price_unit = self._quote_surface.price_unit
        quote_df = pd.DataFrame(np.nan, index=np.arange(self._quote_surface.n_quotes()), columns=COL_NAMES)
        row_index = 0
        for qs in self._quote_surface.slices:
            for q in qs.quotes:
                quote_df[EXPIRY_KEY].iloc[row_index] = qs.expiry
                
                q_trans = transform_quote(q=q, price_unit=current_price_unit, target_price_unit=price_unit, 
                                          expiry=qs.expiry, discount_factor=qs.discount_factor, forward=qs.forward)
                quote_df[STRIKE_KEY].iloc[row_index] = q_trans.get_transformed_strike(strike_trans, forward=qs.forward)
                quote_df[MID_KEY].iloc[row_index] = q_trans(Side.mid)
                quote_df[BID_KEY].iloc[row_index] = q_trans.bid
                quote_df[ASK_KEY].iloc[row_index] = q_trans.ask
                quote_df[LIQ_KEY].iloc[row_index] = q_trans.liq_proxy

                row_index += 1

        return quote_df
