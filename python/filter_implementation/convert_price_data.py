''' Goal: This module converts price data from lists to quote lists and quote surfaces for implementation of the
          examples in "Arbitrage-Based Filtering of Option Price Data."

    Author: Karim Moussa (2017) '''


from .volatility_functions import implied_vol_for_discounted_option, discounted_black
from .quote import Quote
from .quote_slice import QuoteSlice
from .quote_surface import QuoteSurface
from .filter_constants import CALL_ONE_ELSE_PUT_MINUS_ONE


def compute_ranking_quantity(strike, forward):
    return abs(strike - forward)


def data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor):
    ''' Goal: This function takes a list filled with tuples of strikes and implied Black vols, and returns
        a corresponding quote slice object
    '''

    quote_list = []
    list_size = len(strike_vol_list)

    for i in range(list_size):
        strike = strike_vol_list[i][0]
        implied_vol = strike_vol_list[i][1]

        call_premium = discounted_black(forward, strike, implied_vol, expiry, discount_factor,
                                        CALL_ONE_ELSE_PUT_MINUS_ONE)
        ranking_coordinate = compute_ranking_quantity(strike, forward)

        quote_list.append( Quote(strike, expiry, implied_vol, call_premium, ranking_coordinate, forward) )

    return QuoteSlice(discount_factor, forward, expiry, quote_list)


def strikes_vols_and_premia_to_quote_surface(strike_premium_lists, expiries, forwards, discount_factors):
    ''' Goal: This function transforms a set of strikes and call premia for multiple expiries to a QuoteSurface objects

        Inputs: strike_premium_lists: a list filled with lists that contain tuples of strikes and call premia
                expiries: a list containing the expiries corresponding to the elements in strike_premium_lists
                forwards: a list containing the forwards corresponding to the elements in strike_premium_lists
                discount_factors: a list containing the discount_factors corresponding to the elements in
                    strike_premium_lists
    '''

    quote_slices = []
    expiries.sort()

    expiry_length = len(expiries)

    for i in range(0, expiry_length):
        quote_list = []
        expiry = expiries[i]
        forward = forwards[i]
        discount_factor = discount_factors[i]

        for (strike, premium) in strike_premium_lists[i]:
            ranking_quantity = compute_ranking_quantity(strike, forwards[i])
            implied_vol = implied_vol_for_discounted_option(premium, forward, strike, expiry, discount_factor,
                                                            CALL_ONE_ELSE_PUT_MINUS_ONE)
            quote_list.append(Quote(strike, expiry, implied_vol, premium, ranking_quantity, forward) )

        quote_slice_object = QuoteSlice(discount_factor, forward, expiry, quote_list)
        quote_slices.append(quote_slice_object)

    return QuoteSurface(quote_slices)