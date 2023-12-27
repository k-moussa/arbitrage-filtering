""" This module contains functionality to transform quotes. """

import numpy as np
from copy import copy
from .quote_structures import Quote
from ..globals import PriceUnit, StrikeUnit
from .volatility_functions import implied_vol_for_discounted_option, discounted_black


def transform_quote(q: Quote,
                    price_unit: PriceUnit,
                    target_price_unit: PriceUnit,
                    strike_unit: StrikeUnit, 
                    target_strike_unit: StrikeUnit,
                    expiry: float,
                    discount_factor: float,
                    forward: float,
                    in_place: bool) -> Quote:

    if price_unit is target_price_unit and strike_unit is target_strike_unit:
        return q

    if in_place:
        trans_q = q
    else:
        trans_q = copy(q)

    _update_strike_unit(strike_unit=strike_unit,
                        target_strike_unit=target_strike_unit,
                        forward=forward,
                        q=trans_q)

    _update_price_unit(price_unit=price_unit,
                       target_price_unit=target_price_unit,
                       expiry=expiry,
                       discount_factor=discount_factor,
                       forward=forward,
                       q=trans_q)

    return trans_q


def _update_strike_unit(strike_unit: StrikeUnit,
                        target_strike_unit,
                        forward: float,
                        q: Quote):

    if strike_unit is target_strike_unit:
        return

    strike = q.strike
    if strike_unit is not StrikeUnit.strike:  # map to strike
        if strike_unit is StrikeUnit.moneyness:
            strike *= forward
        elif strike_unit is StrikeUnit.log_moneyness:
            strike = np.exp(strike) * forward
        else:
            raise RuntimeError(f"Unhandled strike_unit {strike_unit.name}")

    if target_strike_unit is StrikeUnit.strike:
        q.strike = strike
    elif target_strike_unit is StrikeUnit.moneyness:
        q.strike = strike / forward
    elif target_strike_unit is StrikeUnit.log_moneyness:
        q.strike = np.log(strike / forward)
    else:
        raise RuntimeError(f"Unhandled target_strike_unit {target_strike_unit.name}")


def _update_price_unit(price_unit: PriceUnit,
                       target_price_unit: PriceUnit,
                       expiry: float,
                       discount_factor: float,
                       forward: float,
                       q: Quote):

    if price_unit is target_price_unit:
        return

    if price_unit is not PriceUnit.call:
        if price_unit is PriceUnit.vol:
            q.bid = discounted_black(forward=forward, strike=q.strike, vol=q.bid, expiry=expiry,
                                     discount_factor=discount_factor, call_one_else_put_minus_one=1)
            q.ask = discounted_black(forward=forward, strike=q.strike, vol=q.ask, expiry=expiry,
                                     discount_factor=discount_factor, call_one_else_put_minus_one=1)
        elif price_unit is PriceUnit.normalized_call:
            raise RuntimeError("normalized call as input not implemented.")  # todo:  define strike 0 call and re-use

    if target_price_unit is PriceUnit.call:
        return q
    elif target_price_unit is PriceUnit.vol:
        q.bid = implied_vol_for_discounted_option(discounted_option_price=q.bid, forward=forward,
                                                  strike=q.strike, expiry=expiry, discount_factor=discount_factor,
                                                  call_one_else_put_minus_one=1)
        q.ask = implied_vol_for_discounted_option(discounted_option_price=q.ask, forward=forward,
                                                  strike=q.strike, expiry=expiry, discount_factor=discount_factor,
                                                  call_one_else_put_minus_one=1)
    elif target_price_unit is PriceUnit.normalized_call:
        raise RuntimeError("normalized call as output not implemented.")  # todo:  define strike 0 call and re-use
