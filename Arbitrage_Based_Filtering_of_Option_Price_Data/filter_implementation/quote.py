''' Goal: This module defines a Quote object used in the implementation of "Arbitrage-Based
             Filtering of Option Price Data."

    Author: Karim Moussa (2017) '''


from .volatility_functions import implied_vol_for_discounted_option
from .filter_constants import CALL_ONE_ELSE_PUT_MINUS_ONE


class Quote:
    def __init__(self, strike, expiry, implied_vol, call_premium, ranking_quantity, forward):
        self.strike = strike
        self.expiry = expiry
        self.implied_vol = implied_vol
        self.call_premium = call_premium
        self.moneyness = strike / forward
        self.ranking_quantity = ranking_quantity  # The quote importance must be descending in the ranking quantity
        self.is_adjusted = False
        self.adjustment_call_premium = 0.0
        self.adjustment_implied_vol = 0.0


    def __lt__(self, other):  # < operator
        """ Overloads the < operator to allow for using the bisection module for efficient insertion and
        lookup based on the strike. """

        return self.strike < other.strike


    def __eq__(self, other):  # == operator
        """ Overloads the == operator to allow for using the bisection module for efficient insertion and
            lookup based on the strike. """

        return self.strike == other.strike


    def adjust(self, new_premium, forward, discount_factor):
        self.adjustment_call_premium = new_premium - self.call_premium
        self.call_premium = new_premium

        new_implied_vol = implied_vol_for_discounted_option(self.call_premium, forward, self.strike, self.expiry,
                                                            discount_factor, CALL_ONE_ELSE_PUT_MINUS_ONE)
        self.adjustment_implied_vol = new_implied_vol - self.implied_vol
        self.implied_vol = new_implied_vol

        self.is_adjusted = True