''' Goal: This module defines the volatility functions used for "Arbitrage-Based Filtering of Option Price Data.";
    the functions depend on Peter Jackael's proposed implied volatility solver and Black function from
    "Let's Be Rational" as implemented in https://github.com/vollib/lets_be_rational

    Author: Karim Moussa (2017) '''


from math import inf
from Arbitrage_Based_Filtering_of_Option_Price_Data.py_lets_be_rational.lets_be_rational import black, \
    implied_volatility_from_a_transformed_rational_guess
from Arbitrage_Based_Filtering_of_Option_Price_Data.py_lets_be_rational.exceptions import AboveMaximumException, \
    BelowIntrinsicException


def implied_vol_for_discounted_option(discounted_option_price, forward, strike, expiry, discount_factor,
                                      call_one_else_put_minus_one):
    """ This function calls the implied_volatility solver from Peter Jackael's "Let's be rational", while handling
        the AboveMaximumException and BelowIntrinsicException exceptions to ensure that the filtering procedure is not
        interrupted after round-off errors or unacceptable starting data that violates the theoretical European call
        price bounds. """

    undiscounted_price = discounted_option_price / discount_factor

    try:
        implied_vol = implied_volatility_from_a_transformed_rational_guess(undiscounted_price, forward, strike, expiry,
                                                                           call_one_else_put_minus_one)
    except AboveMaximumException:
        implied_vol = inf
    except BelowIntrinsicException:
        implied_vol = 0.0
    return implied_vol


def discounted_black(forward, strike, sigma, expiry, discount_factor, call_one_else_put_minus_one):
    return discount_factor*black(forward, strike, sigma, expiry, call_one_else_put_minus_one)



