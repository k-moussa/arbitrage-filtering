""" This module contains functionality to transform quotes. """

import numpy as np
from copy import copy, deepcopy
from .quote_structures import Quote, QuoteSurface
from ..globals import PriceUnit, StrikeUnit
from .volatility_functions import implied_vol_for_discounted_option, discounted_black
from .zero_strike_computation import compute_zero_strike_call_value


def transform_quote_surface(quote_surface: QuoteSurface,
                            target_price_unit: PriceUnit,
                            target_strike_unit: StrikeUnit,
                            in_place: bool) -> QuoteSurface:
    
    if in_place:
        trans_quote_surface = quote_surface
    else:
        trans_quote_surface = deepcopy(quote_surface)

    for qs in trans_quote_surface.slices:
        for q in qs.quotes:
            transform_quote(q=q,
                            price_unit=quote_surface.price_unit,
                            target_price_unit=target_price_unit,
                            strike_unit=quote_surface.strike_unit,
                            target_strike_unit=target_strike_unit,
                            expiry=qs.expiry,
                            discount_factor=qs.discount_factor,
                            forward=qs.forward,
                            in_place=True)

    trans_quote_surface.price_unit = target_price_unit
    trans_quote_surface.strike_unit = target_strike_unit
    return trans_quote_surface


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

    actual_strike = _get_actual_strike(trans_q, forward=forward, current_strike_unit=strike_unit)
    _update_strike_unit(actual_strike=actual_strike,
                        strike_unit=strike_unit,
                        target_strike_unit=target_strike_unit,
                        forward=forward,
                        q=trans_q)

    _update_price_unit(actual_strike=actual_strike,
                       price_unit=price_unit,
                       target_price_unit=target_price_unit,
                       expiry=expiry,
                       discount_factor=discount_factor,
                       forward=forward,
                       q=trans_q)

    return trans_q


def _get_actual_strike(q: Quote, 
                       forward: float,
                       current_strike_unit: StrikeUnit) -> float:
    
    strike = q.strike
    if current_strike_unit is not StrikeUnit.strike:  # map to strike
        if current_strike_unit is StrikeUnit.moneyness:
            strike *= forward
        elif current_strike_unit is StrikeUnit.log_moneyness:
            strike = np.exp(strike) * forward
        else:
            raise RuntimeError(f"Unhandled strike_unit {current_strike_unit.name}")
        
    return strike


def _update_strike_unit(actual_strike: float,
                        strike_unit: StrikeUnit,
                        target_strike_unit,
                        forward: float,
                        q: Quote):

    if strike_unit is target_strike_unit:
        return

    if target_strike_unit is StrikeUnit.strike:
        q.strike = actual_strike
    elif target_strike_unit is StrikeUnit.moneyness:
        q.strike = actual_strike / forward
    elif target_strike_unit is StrikeUnit.log_moneyness:
        q.strike = np.log(actual_strike / forward)
    else:
        raise RuntimeError(f"Unhandled target_strike_unit {target_strike_unit.name}")


def _update_price_unit(actual_strike: float,
                       price_unit: PriceUnit,
                       target_price_unit: PriceUnit,
                       expiry: float,
                       discount_factor: float,
                       forward: float,
                       q: Quote):

    if price_unit is target_price_unit:
        return

    if price_unit is not PriceUnit.call:
        if price_unit in (PriceUnit.vol, PriceUnit.total_var):
            if price_unit is PriceUnit.total_var:  # map to vol
                q.bid = np.sqrt(q.bid / expiry)
                q.ask = np.sqrt(q.ask / expiry)

            q.bid = discounted_black(forward=forward, strike=actual_strike, vol=q.bid, expiry=expiry,
                                     discount_factor=discount_factor, call_one_else_put_minus_one=1)
            q.ask = discounted_black(forward=forward, strike=actual_strike, vol=q.ask, expiry=expiry,
                                     discount_factor=discount_factor, call_one_else_put_minus_one=1)
        elif price_unit is PriceUnit.normalized_call:
            zero_strike_call = compute_zero_strike_call_value(discount_factor=discount_factor, forward=forward)
            q.bid *= zero_strike_call
            q.ask *= zero_strike_call

    if target_price_unit is PriceUnit.call:
        return q
    elif target_price_unit in (PriceUnit.vol, PriceUnit.total_var):
        q.bid = implied_vol_for_discounted_option(discounted_option_price=q.bid, forward=forward,
                                                  strike=actual_strike, expiry=expiry, discount_factor=discount_factor,
                                                  call_one_else_put_minus_one=1)
        q.ask = implied_vol_for_discounted_option(discounted_option_price=q.ask, forward=forward,
                                                  strike=actual_strike, expiry=expiry, discount_factor=discount_factor,
                                                  call_one_else_put_minus_one=1)
        if target_price_unit is PriceUnit.total_var:
            q.bid = (q.bid ** 2) * expiry
            q.ask = (q.ask ** 2) * expiry
    elif target_price_unit is PriceUnit.normalized_call:
        zero_strike_call = compute_zero_strike_call_value(discount_factor=discount_factor, forward=forward)
        q.bid /= zero_strike_call
        q.ask /= zero_strike_call
