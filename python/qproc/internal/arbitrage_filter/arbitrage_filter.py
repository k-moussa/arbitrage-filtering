""" This module implements the various arbitrage filters. """

import numpy as np
from typing import Optional, List
from abc import ABC, abstractmethod
from .globals import ArbitrageFilter
from .arbitrage_free_set import ArbitrageFreeSet
from ..quote_structures import QuoteSurface, QuoteSlice, Quote, Side
from ...globals import FloatOrArray


class InternalArbitrageFilter(ArbitrageFilter, ABC):
    def __init__(self,
                 quote_surface: QuoteSurface,
                 smoothing_param: Optional[FloatOrArray]):

        self.arbitrage_free_sets: List[ArbitrageFreeSet] = []
        self.quote_surface: QuoteSurface = quote_surface

        self._slice_index: Optional[int] = None
        self._current_liq_sorted_quotes: List[Quote] = []
        self._current_a: ArbitrageFreeSet = ArbitrageFreeSet()
        self._current_a_complement: List[Quote] = []

        if smoothing_param is None:
            self.smoothing_params: np.ndarray = np.full(shape=(self.quote_surface.n_expiries()), fill_value=np.nan)
        elif isinstance(smoothing_param, float):
            self.smoothing_params: np.ndarray = np.full(shape=(self.quote_surface.n_expiries()),
                                                        fill_value=smoothing_param)
        else:
            self.smoothing_params = smoothing_param

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
        self.set_liquidity_sorted_quotes()
        self.process_quote_slice()
        smoothing_param = self.smoothing_params[self._slice_index]
        self.adjust_remaining_quotes(smoothing_param)

    def set_liquidity_sorted_quotes(self):
        current_quote_slice = self._get_current_quote_slice()
        self._current_liq_sorted_quotes = current_quote_slice.quotes
        self._current_liq_sorted_quotes.sort(key=lambda q: q.liq_proxy)
        
    def _get_current_quote_slice(self) -> QuoteSlice:
        return self.quote_surface.slices[self._slice_index]

    def process_quote_slice(self):
        n_quotes = len(self._current_liq_sorted_quotes)
        for i in range(n_quotes):
            self.perform_process_iteration()

    def perform_process_iteration(self):
        q = self._current_liq_sorted_quotes.pop(0)
        if not self._current_a.add_quote_if_feasible(q):
            self._current_a_complement.append(q)
            
    def adjust_remaining_quotes(self, smoothing_param: float):
        n_remaining_quotes = len(self._current_a_complement)
        for i in range(n_remaining_quotes):
            self.perform_adjust_iteration(smoothing_param)
        
    def perform_adjust_iteration(self, smoothing_param: float):
        q = self._current_a_complement.pop(0)
        lower_bound = self._current_a.compute_lower_bound(q)
        upper_bound = self._current_a.compute_upper_bound(q)

        if q.mid() < lower_bound:
            adjusted_price = lower_bound + smoothing_param * (upper_bound - lower_bound)
        elif q.mid() > upper_bound:
            adjusted_price = lower_bound + (1.0 - smoothing_param) * (upper_bound - lower_bound)
        else:
            raise RuntimeError("adjust is only meant for infeasible quotes")

        q.set_price(price=adjusted_price, side=Side.mid)
        self._current_a.add_quote_if_feasible(q)
            