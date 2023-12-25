""" This module implements the InternalQuoteProcessor class. """

from typing import Optional
from ..globals import *
from .quote_structures import QuoteSurface, QuoteSlice, Quote
from .quote_map import transform_quote

N_COLS: final = 6


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

            bid, ask = sided_option_prices[i]
            strike = strikes[i]
            liq_proxy = self._get_liquidity_proxy(liquidity_proxies[i], strike=strike, forward=forward)
            q = Quote(bid=bid, ask=ask, strike=strike, liq_proxy=liq_proxy)
            quote_slice.add_quote(q)

    @staticmethod
    def _get_liquidity_proxy(liq_proxy: Optional[float],
                             strike: float,
                             forward: float) -> float:

        if liq_proxy is None:
            liq_proxy = -np.abs(strike/forward - 1.0)

        return liq_proxy

    def get_quote_matrix(self,
                         strike_trans: StrikeTransform,
                         price_unit: PriceUnit) -> np.ndarray:

        current_price_unit = self._quote_surface.price_unit
        quote_matrix = np.zeros(shape=(self._quote_surface.n_quotes(), N_COLS))
        row_index = 0
        for qs in self._quote_surface.slices:
            for q in qs.quotes:
                quote_matrix[row_index, EXPIRY_INDEX] = qs.expiry
                
                q_trans = transform_quote(q=q, price_unit=current_price_unit, target_price_unit=price_unit, 
                                          expiry=qs.expiry, discount_factor=qs.discount_factor, forward=qs.forward)
                quote_matrix[row_index, STRIKE_INDEX] = q_trans.get_transformed_strike(strike_trans, forward=qs.forward)
                quote_matrix[row_index, MID_INDEX] = q_trans(Side.mid)  
                quote_matrix[row_index, BID_INDEX] = q_trans.bid
                quote_matrix[row_index, ASK_INDEX] = q_trans.ask
                quote_matrix[row_index, LIQ_INDEX] = q_trans.liq_proxy

                row_index += 1

        return quote_matrix
