""" This module defines the ArbitrageFreeSet class. 

    Remark: The implementation assumes that the quotes are normalized call prices. """

import bisect
import numpy as np
from typing import List, final
from qproc.internal.sorting_algorithms import find_lt, find_gt, find_le
from ..quote_structures import Quote, QuoteSlice, QuoteSurface

QUOTE_0: final = Quote(bid=1.0, ask=1.0, strike=0.0, liq_proxy=np.nan)
QUOTE_INF: final = Quote(bid=0.0, ask=0.0, strike=np.inf, liq_proxy=np.nan)


class ArbitrageFreeSet(QuoteSlice):
    def __init__(self, expiry: float):
        super().__init__(expiry=expiry)
        self.quotes.append(QUOTE_0)
        self.quotes.append(QUOTE_INF)

    def get_arbitrage_free_quotes(self, exclude_strikes_0_and_inf: bool) -> List[Quote]:
        arbitrage_free_quotes = self.quotes
        if exclude_strikes_0_and_inf:
            return arbitrage_free_quotes[1:-1]
        else:
            return arbitrage_free_quotes

    def compute_lower_bound(self, q: Quote) -> float:
        left_adjacent_quote = self._get_left_adjacent_quote(q)
        left_difference_quotient = self._compute_left_difference_quotient(q)
        lower_bound_from_left_difference_quotient = max(left_adjacent_quote.mid() + left_difference_quotient * 
                                                        (q.strike - left_adjacent_quote.strike), 0.0)

        right_adjacent_quote = self._get_right_adjacent_quote(q)
        right_difference_quotient = self._compute_right_difference_quotient(q)
        lower_bound_from_right_difference_quotient = right_adjacent_quote.mid()
        if np.isfinite(right_adjacent_quote.strike):  # handle 0.0 * inf = nan
            lower_bound_from_right_difference_quotient -= right_difference_quotient * \
                                                          (right_adjacent_quote.strike - q.strike)

        return max(lower_bound_from_left_difference_quotient, lower_bound_from_right_difference_quotient)

    def _get_left_adjacent_quote(self, q: Quote) -> Quote:
        return find_lt(self.quotes, q)

    def _compute_left_difference_quotient(self, q: Quote) -> float:
        if self._are_two_points_left_of_quote(q):
            first_quote_to_left = self._get_left_adjacent_quote(q)
            second_quote_to_left = self._get_left_adjacent_quote(first_quote_to_left)

            return (first_quote_to_left.mid() - second_quote_to_left.mid()) / \
                   (first_quote_to_left.strike - second_quote_to_left.strike)
        else:
            return -1.0
        
    def _are_two_points_left_of_quote(self, q: Quote) -> bool:
        return self.quotes[1].strike < q.strike
    
    def _get_right_adjacent_quote(self, q: Quote) -> Quote:
        return find_gt(self.quotes, q)
    
    def _compute_right_difference_quotient(self, q: Quote) -> float:
        
        if self._are_two_points_right_of_quote(q):
            first_quote_to_right = self._get_right_adjacent_quote(q)
            second_quote_to_right = self._get_right_adjacent_quote(first_quote_to_right)

            return (first_quote_to_right.mid() - second_quote_to_right.mid()) / \
                   (first_quote_to_right.strike - second_quote_to_right.strike)
        else:
            return 0.0
        
    def _are_two_points_right_of_quote(self, q: Quote) -> bool:
        return self.quotes[-2].strike > q.strike
    
    def compute_upper_bound(self, q: Quote) -> float:
        left_adjacent_quote = self._get_left_adjacent_quote(q)

        if self._is_strike_of_right_adjacent_quote_finite(q):
            right_adjacent_quote = self._get_right_adjacent_quote(q)

            interpolated_call_premium = ((right_adjacent_quote.strike - q.strike) * left_adjacent_quote.mid() +
                                         (q.strike - left_adjacent_quote.strike) * right_adjacent_quote.mid()) / \
                                        (right_adjacent_quote.strike - left_adjacent_quote.strike)
            return interpolated_call_premium
        else:
            return left_adjacent_quote.mid()

    def _is_strike_of_right_adjacent_quote_finite(self, q: Quote) -> bool:
        right_adjacent_quote = self._get_right_adjacent_quote(q)
        return np.isfinite(right_adjacent_quote.strike)


class ArbitrageFreeCollection:
    def __init__(self):
        self.sets: List[ArbitrageFreeSet] = []

    def add_set(self, a: ArbitrageFreeSet):
        bisect.insort_right(self.sets, a)
        
    def get_set(self, expiry: float) -> ArbitrageFreeSet:
        """ Returns the quote set for the given expiry; raises a runtime error if expiry is not equivalent. """

        dummy_set_for_indexing = ArbitrageFreeSet(expiry=expiry)
        a = find_le(self.sets, dummy_set_for_indexing)
        if a.expiry != expiry:
            raise RuntimeError("expiry does not match any of the quote expiries")

        return a
