""" This module contains functionality to transform quotes. """

from copy import copy
from .quote_structures import Quote
from ..globals import PriceUnit
from .volatility_functions import implied_vol_for_discounted_option, discounted_black


def transform_quote(q: Quote,
                    price_unit: PriceUnit,
                    target_price_unit: PriceUnit,
                    expiry: float,
                    discount_factor: float,
                    forward: float) -> Quote:

    if price_unit is target_price_unit:
        return q

    trans_q = copy(q)
    if price_unit is not PriceUnit.call:
        if price_unit is PriceUnit.vol:
            trans_q.bid = discounted_black(forward=forward, strike=q.strike, vol=q.bid, expiry=expiry, 
                                           discount_factor=discount_factor, call_one_else_put_minus_one=1)
            trans_q.ask = discounted_black(forward=forward, strike=q.strike, vol=q.ask, expiry=expiry, 
                                           discount_factor=discount_factor, call_one_else_put_minus_one=1)
        elif price_unit is PriceUnit.normalized_call:
            raise RuntimeError("normalized call as input not implemented.")  # todo:  define strike 0 call and re-use
        
    if target_price_unit is PriceUnit.call:
        return trans_q
    elif target_price_unit is PriceUnit.vol:
        trans_q.bid = implied_vol_for_discounted_option(discounted_option_price=trans_q.bid, forward=forward, 
                                                        strike=q.strike, expiry=expiry, discount_factor=discount_factor,
                                                        call_one_else_put_minus_one=1)
        trans_q.ask = implied_vol_for_discounted_option(discounted_option_price=trans_q.ask, forward=forward,
                                                        strike=q.strike, expiry=expiry, discount_factor=discount_factor,
                                                        call_one_else_put_minus_one=1)
    elif target_price_unit is PriceUnit.normalized_call:
        raise RuntimeError("normalized call as output not implemented.")  # todo:  define strike 0 call and re-use

    return trans_q
