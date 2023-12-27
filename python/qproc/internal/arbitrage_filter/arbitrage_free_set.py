""" This module defines the ArbitrageFreeSet class. 

    Remark: The implementation assumes that the quotes are normalized call prices. """

import bisect
import numpy as np
from typing import List, final
from .sorting_algorithms import find_lt, find_gt
from ..quote_structures import Quote

QUOTE_0: final = Quote(bid=1.0, ask=1.0, strike=0.0, liq_proxy=np.nan)
QUOTE_INF: final = Quote(bid=0.0, ask=0.0, strike=np.inf, liq_proxy=np.nan)


class ArbitrageFreeSet:
    def __init__(self):
        self._sorted_quotes: List[Quote] = [QUOTE_0, QUOTE_INF]

    def get_arbitrage_free_quotes(self, exclude_strikes_0_and_inf: bool) -> List[Quote]:
        arbitrage_free_quotes = self._sorted_quotes
        if exclude_strikes_0_and_inf:
            return arbitrage_free_quotes[1:-1]
        else:
            return arbitrage_free_quotes

    def add_quote_if_feasible(self, q: Quote) -> bool:
        lower_bound = self.compute_lower_bound(q)
        upper_bound = self.compute_upper_bound(q)
        is_quote_feasible = lower_bound <= q.mid() <= upper_bound
        if is_quote_feasible:
            bisect.insort_left(self._sorted_quotes, q)

        return is_quote_feasible

    def compute_lower_bound(self, q: Quote) -> float:
        left_adjacent_quote = self._get_left_adjacent_quote(q)
        left_difference_quotient = self._compute_left_difference_quotient(q)
        lower_bound_from_left_difference_quotient = max(left_adjacent_quote.mid() + left_difference_quotient * 
                                                        (q.strike - left_adjacent_quote.strike), 0.0)

        right_adjacent_quote = self._get_right_adjacent_quote(q)
        right_difference_quotient = self._compute_right_difference_quotient(q)
        lower_bound_from_right_difference_quotient = right_adjacent_quote.mid() - right_difference_quotient * \
            (right_adjacent_quote.strike - q.strike)

        return max(lower_bound_from_left_difference_quotient, lower_bound_from_right_difference_quotient)

    def _get_left_adjacent_quote(self, q: Quote) -> Quote:
        return find_lt(self._sorted_quotes, q)

    def _compute_left_difference_quotient(self, q: Quote) -> float:
        if self._are_two_points_left_of_quote(q):
            first_quote_to_left = self._get_left_adjacent_quote(q)
            second_quote_to_left = self._get_left_adjacent_quote(first_quote_to_left)

            return (first_quote_to_left.mid() - second_quote_to_left.mid()) / \
                   (first_quote_to_left.strike - second_quote_to_left.strike)
        else:
            return -1.0
        
    def _are_two_points_left_of_quote(self, q: Quote) -> bool:
        return self._sorted_quotes[1].strike < q.strike
    
    def _get_right_adjacent_quote(self, q: Quote) -> Quote:
        return find_gt(self._sorted_quotes, q)
    
    def _compute_right_difference_quotient(self, q: Quote) -> float:
        
        if self._are_two_points_right_of_quote(q):
            first_quote_to_right = self._get_right_adjacent_quote(q)
            second_quote_to_right = self._get_right_adjacent_quote(first_quote_to_right)

            return (first_quote_to_right.mid() - second_quote_to_right.mid()) / \
                   (first_quote_to_right.strike - second_quote_to_right.strike)
        else:
            return 0.0
        
    def _are_two_points_right_of_quote(self, q: Quote) -> bool:
        return self._sorted_quotes[-2].strike > q.strike
    
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