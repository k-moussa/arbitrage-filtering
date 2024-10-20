""" This module collects functionality to transform strikes, prices, and quotes to desired units. """

import numpy as np
from typing import final
from copy import copy, deepcopy
from computils import ScalarOrArray
from ..globals import StrikeUnit, PriceUnit
from .quote_structures import Quote
from .volatility_functions import implied_vol_for_discounted_option, discounted_black
from .zero_strike_computation import compute_zero_strike_call_value

VOL_UNITS: final = (PriceUnit.vol, PriceUnit.total_var)


def transform_strike(strike: ScalarOrArray,
                     input_strike_unit: StrikeUnit,
                     output_strike_unit: StrikeUnit,
                     forward: ScalarOrArray) -> ScalarOrArray:

    if input_strike_unit is output_strike_unit:
        return strike

    strike = deepcopy(strike)   # do not overwrite input

    # map to actual strike
    if input_strike_unit is not StrikeUnit.strike:  # map to strike
        if input_strike_unit is StrikeUnit.moneyness:
            strike *= forward
        elif input_strike_unit is StrikeUnit.log_moneyness:
            strike = np.exp(strike) * forward
        else:
            raise RuntimeError(f"Unhandled input_strike_unit {input_strike_unit.name}")

    if output_strike_unit is StrikeUnit.strike:
        return strike
    elif output_strike_unit is StrikeUnit.moneyness:
        return strike / forward
    elif output_strike_unit is StrikeUnit.log_moneyness:
        return np.log(strike / forward)
    else:
        raise RuntimeError(f"Unhandled output_strike_unit {output_strike_unit.name}")


def transform_price(strike: ScalarOrArray,
                    strike_unit: StrikeUnit,
                    price: ScalarOrArray,
                    input_price_unit: PriceUnit,
                    output_price_unit: PriceUnit,
                    expiry: float,
                    discount_factor: float,
                    forward: float) -> ScalarOrArray:

    actual_strike = transform_strike(strike=strike, input_strike_unit=strike_unit,
                                     output_strike_unit=StrikeUnit.strike, forward=forward)

    if not isinstance(actual_strike, np.ndarray):  # scalar
        return _get_single_price(
            actual_strike=actual_strike, price=price, input_price_unit=input_price_unit,
            output_price_unit=output_price_unit, expiry=expiry, discount_factor=discount_factor, forward=forward)
    else:
        output_prices = np.full(shape=actual_strike.shape, fill_value=np.nan)
        for i in range(actual_strike.size):
            output_prices[i] = _get_single_price(
                actual_strike=actual_strike[i], price=price[i], input_price_unit=input_price_unit,
                output_price_unit=output_price_unit,  expiry=expiry, discount_factor=discount_factor,
                forward=forward)

        return output_prices


def _get_single_price(actual_strike: float,
                      price: float,
                      input_price_unit: PriceUnit,
                      output_price_unit: PriceUnit,
                      expiry: float,
                      discount_factor: float,
                      forward: float) -> float:

    if input_price_unit is output_price_unit:
        return price

    if input_price_unit in VOL_UNITS and output_price_unit in VOL_UNITS:  # circumvent conversion via call price
        return _transform_vol(price=price, expiry=expiry, input_price_unit=input_price_unit,
                              output_price_unit=output_price_unit)

    if input_price_unit is not PriceUnit.call:
        if input_price_unit in VOL_UNITS:  # map to vol
            vol = _transform_vol(price=price, expiry=expiry, input_price_unit=input_price_unit,
                                 output_price_unit=PriceUnit.vol)
            price = discounted_black(forward=forward, strike=actual_strike, vol=vol, expiry=expiry,
                                     discount_factor=discount_factor, call_one_else_put_minus_one=1)
        elif input_price_unit is PriceUnit.undiscounted_call:
            price *= discount_factor
        elif input_price_unit is PriceUnit.normalized_call:
            zero_strike_call = compute_zero_strike_call_value(discount_factor=discount_factor, forward=forward)
            price *= zero_strike_call

    if output_price_unit is PriceUnit.call:
        return price
    elif output_price_unit in VOL_UNITS:
        price = implied_vol_for_discounted_option(discounted_option_price=price, forward=forward,
                                                  strike=actual_strike, expiry=expiry,
                                                  discount_factor=discount_factor,
                                                  call_one_else_put_minus_one=1)
        price = _transform_vol(price=price, expiry=expiry, input_price_unit=PriceUnit.vol,
                               output_price_unit=output_price_unit)
    elif output_price_unit is PriceUnit.undiscounted_call:
        price /= discount_factor
    elif output_price_unit is PriceUnit.normalized_call:
        zero_strike_call = compute_zero_strike_call_value(discount_factor=discount_factor, forward=forward)
        price /= zero_strike_call

    return price


def _transform_vol(price: float,
                   expiry: float,
                   input_price_unit: PriceUnit,
                   output_price_unit: PriceUnit) -> float:

    if input_price_unit is output_price_unit:
        return price
    elif input_price_unit is PriceUnit.vol and output_price_unit is PriceUnit.total_var:
        return (price ** 2) * expiry
    elif input_price_unit is PriceUnit.total_var and output_price_unit is PriceUnit.vol:
        return np.sqrt(price / expiry)
    else:
        raise RuntimeError("One of the price units are not of the vol type.")


def transform_quote(q: Quote,
                    input_price_unit: PriceUnit,
                    output_price_unit: PriceUnit,
                    input_strike_unit: StrikeUnit,
                    output_strike_unit: StrikeUnit,
                    expiry: float,
                    discount_factor: float,
                    forward: float,
                    in_place: bool) -> Quote:

    if input_price_unit is output_price_unit and input_strike_unit is output_strike_unit:
        return q

    if in_place:
        trans_q = q
    else:
        trans_q = copy(q)

    actual_strike = transform_strike(trans_q.strike, input_strike_unit=input_strike_unit,
                                     output_strike_unit=StrikeUnit.strike, forward=forward)

    trans_q.strike = transform_strike(strike=actual_strike,
                                      input_strike_unit=StrikeUnit.strike,
                                      output_strike_unit=output_strike_unit,
                                      forward=forward)

    _update_price_unit(actual_strike=actual_strike,
                       input_price_unit=input_price_unit,
                       output_price_unit=output_price_unit,
                       expiry=expiry,
                       discount_factor=discount_factor,
                       forward=forward,
                       q=trans_q)

    return trans_q


def _update_price_unit(actual_strike: float,
                       input_price_unit: PriceUnit,
                       output_price_unit: PriceUnit,
                       expiry: float,
                       discount_factor: float,
                       forward: float,
                       q: Quote):

    q.bid = transform_price(
        strike=actual_strike, strike_unit=StrikeUnit.strike, price=q.bid, input_price_unit=input_price_unit,
        output_price_unit=output_price_unit, expiry=expiry, discount_factor=discount_factor, forward=forward)
    q.ask = transform_price(
        strike=actual_strike, strike_unit=StrikeUnit.strike, price=q.ask, input_price_unit=input_price_unit,
        output_price_unit=output_price_unit, expiry=expiry, discount_factor=discount_factor, forward=forward)
