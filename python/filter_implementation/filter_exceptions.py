''' Goal: This module implements a the quote-related exceptions for the implementation of "Arbitrage-Based
             Filtering of Option Price Data."

    Author: Karim Moussa (2017) '''


class LowerBoundMoneynessTooHighException(Exception):
    def __init__(self):
        Exception.__init__(self, "No feasible solution possible: lower bound for moneyness exceeds upper bound for "
                                 "strike.")
        self.value = None


class PreviousPremiumTooHighException(Exception):
    def __init__(self):
        Exception.__init__(self, "No feasible solution possible: premium at previous expiry exceeds current expiry's "
                                 "upper bound.")
        self.value = None