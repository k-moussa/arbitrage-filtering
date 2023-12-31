""" This module implements the various arbitrage filters. """

import numpy as np
from typing import Optional, List, Tuple
from .globals import ArbitrageFilter
from .arbitrage_free_set import ArbitrageFreeSet, ArbitrageFreeCollection
from ..quote_structures import QuoteSurface, QuoteSlice, Quote, Side


class StrikeFilter(ArbitrageFilter):
    def __init__(self,
                 quote_surface: QuoteSurface,
                 smoothing_param: Optional[float],
                 smoothing_param_grid: Tuple[float]):

        self.arbitrage_free_collection: ArbitrageFreeCollection = ArbitrageFreeCollection(
            price_unit=quote_surface.price_unit, strike_unit=quote_surface.strike_unit)
        self.quote_surface: QuoteSurface = quote_surface

        self._slice_index: Optional[int] = None
        self._current_liq_sorted_quotes: List[Quote] = None
        self._current_a: ArbitrageFreeSet = None
        self._current_a_complement: List[Quote] = None

        self.smoothing_param_grid: Tuple[float] = smoothing_param_grid
        if smoothing_param is None:
            self.smoothing_params: np.ndarray = np.full(shape=(self.quote_surface.n_expiries()), fill_value=np.nan)
        else:
            self.smoothing_params: np.ndarray = np.full(shape=(self.quote_surface.n_expiries()),
                                                        fill_value=smoothing_param)

    def filter(self):
        for i in range(self.quote_surface.n_expiries()):
            self.advance_slice_index()
            self.filter_quote_slice()

    def advance_slice_index(self):
        if self._slice_index is None:
            self._slice_index = 0
        else:
            self._slice_index += 1

    def filter_quote_slice(self):
        self._initialize_current_variables(expiry=self.quote_surface.slices[self._slice_index].expiry)
        self.set_liquidity_sorted_quotes()
        self.process_quote_slice()
        smoothing_param = self.smoothing_params[self._slice_index]
        self.adjust_remaining_quotes(smoothing_param)

        quote_slice = self._get_current_quote_slice()
        quote_slice.quotes = self._current_a.get_arbitrage_free_quotes(exclude_strikes_0_and_inf=True)

        self.arbitrage_free_collection.add_slice(self._current_a)

    def _initialize_current_variables(self, expiry: float):
        self._current_liq_sorted_quotes: List[Quote] = []
        self._current_a: ArbitrageFreeSet = ArbitrageFreeSet(expiry)
        self._current_a_complement: List[Quote] = []

    def set_liquidity_sorted_quotes(self):
        current_quote_slice = self._get_current_quote_slice()
        self._current_liq_sorted_quotes = current_quote_slice.quotes
        self._current_liq_sorted_quotes.sort(key=lambda q: q.liq_proxy, reverse=True)
        
    def _get_current_quote_slice(self) -> QuoteSlice:
        return self.quote_surface.slices[self._slice_index]

    def process_quote_slice(self):
        n_quotes = len(self._current_liq_sorted_quotes)
        for i in range(n_quotes):
            self.perform_process_iteration()

    def perform_process_iteration(self):
        q = self._current_liq_sorted_quotes.pop(0)
        if not self._add_quote_if_feasible(q):
            self._current_a_complement.append(q)

    def _add_quote_if_feasible(self, q: Quote) -> bool:
        """ If q is feasible w.r.t. to the current arbitrage free set, adds q and returns True, else returns False. """

        lower_bound = self._compute_lower_bound_current_a(q)
        upper_bound = self._compute_upper_bound_current_a(q)
        is_quote_feasible = lower_bound <= q.mid() <= upper_bound
        if is_quote_feasible:
            self._current_a.add_quote(q)

        return is_quote_feasible

    def _compute_lower_bound_current_a(self, q: Quote) -> float:
        return self._current_a.compute_lower_bound(q)
    
    def _compute_upper_bound_current_a(self, q: Quote) -> float:
        return self._current_a.compute_upper_bound(q)
            
    def adjust_remaining_quotes(self, smoothing_param: float):
        n_remaining_quotes = len(self._current_a_complement)
        for i in range(n_remaining_quotes):
            self.perform_adjust_iteration(smoothing_param)
        
    def perform_adjust_iteration(self, smoothing_param: float):
        q = self._current_a_complement.pop(0)
        lower_bound = self._compute_lower_bound_current_a(q)
        upper_bound = self._compute_upper_bound_current_a(q)

        if q.mid() < lower_bound:
            adjusted_price = lower_bound + smoothing_param * (upper_bound - lower_bound)
        elif q.mid() > upper_bound:
            adjusted_price = lower_bound + (1.0 - smoothing_param) * (upper_bound - lower_bound)
        else:
            raise RuntimeError("adjust is only meant for infeasible quotes")

        q.set_price(price=adjusted_price, side=Side.mid)
        self._current_a.add_quote(q)

    def compute_upper_bound(self,
                            expiry: float,
                            trans_strike: float) -> float:

        a = self.arbitrage_free_collection.get_set(expiry)
        dummy_quote_for_indexing = Quote(bid=np.nan, ask=np.nan, strike=trans_strike, liq_proxy=np.nan)
        return a.compute_upper_bound(dummy_quote_for_indexing)
    
    def compute_lower_bound(self,
                            expiry: float,
                            trans_strike: float) -> float:

        a = self.arbitrage_free_collection.get_set(expiry)
        dummy_quote_for_indexing = Quote(bid=np.nan, ask=np.nan, strike=trans_strike, liq_proxy=np.nan)
        return a.compute_lower_bound(dummy_quote_for_indexing)


class ForwardExpiryFilter(StrikeFilter):
    def __init__(self,
                 quote_surface: QuoteSurface,
                 smoothing_param: float,
                 smoothing_param_grid: Tuple[float]):

        super().__init__(quote_surface=quote_surface, smoothing_param=smoothing_param,
                         smoothing_param_grid=smoothing_param_grid)

    def _compute_lower_bound_current_a(self, q: Quote) -> float:
        lower_bound = self._current_a.compute_lower_bound(q)
        for a in self.arbitrage_free_collection.sets():
            lb_from_previous_slice = a.compute_lower_bound(q)
            if lb_from_previous_slice >= lower_bound:
                lower_bound = lb_from_previous_slice

        return lower_bound


class DiscardFilter(StrikeFilter):
    def __init__(self,
                 quote_surface: QuoteSurface,
                 smoothing_param: float,
                 smoothing_param_grid: Tuple[float]):

        super().__init__(quote_surface=quote_surface, smoothing_param=smoothing_param,
                         smoothing_param_grid=smoothing_param_grid)

    def adjust_remaining_quotes(self, smoothing_param: float):
        pass  # do not add remaining quotes.
