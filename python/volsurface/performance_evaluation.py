""" This module allows for computing the pricing errors for a given data set of quotes. """

import numpy as np
from typing import Union, final
import qproc
from .globals import *

STRIKE_UNIT: final = StrikeUnit.strike


def compute_pricing_mae(quote_processor: qproc.OptionQuoteProcessor,
                        vol_surface: VolSurface,
                        price_unit: PriceUnit) -> float:
    """ Computes the mean absolute pricing error in the given unit.

    :param quote_processor:
    :param vol_surface:
    :param price_unit:
    :return:
    """
    pricing_errors = compute_pricing_errors(quote_processor=quote_processor, vol_surface=vol_surface,
                                            price_unit=price_unit, as_arr=True)
    mae = np.mean(np.abs(pricing_errors))
    return float(mae)


def compute_pricing_rmse(quote_processor: qproc.OptionQuoteProcessor,
                         vol_surface: VolSurface,
                         price_unit: PriceUnit) -> float:
    """ Computes the root mean squared pricing error in the given unit.

    :param quote_processor:
    :param vol_surface:
    :param price_unit:
    :return:
    """
    pricing_errors = compute_pricing_errors(quote_processor=quote_processor, vol_surface=vol_surface,
                                            price_unit=price_unit, as_arr=True)
    rmse = np.sqrt(np.mean(pricing_errors ** 2))
    return rmse


def compute_pricing_errors(quote_processor: qproc.OptionQuoteProcessor,
                           vol_surface: VolSurface,
                           price_unit: PriceUnit,
                           as_arr: bool = True) -> Union[np.ndarray, dict]:
    """ Computes the pricing errors of the volatility surface with respect to the raw data.

    :param quote_processor:
    :param vol_surface:
    :param price_unit:
    :param as_arr: if True returns a numpy array with errors.
    :return: either a numpy array with the errors, or a nested dictionary in which each expiry has a dict with strikes
        as keys to identify the errors.
    """

    raw_quotes = quote_processor.get_quotes(strike_unit=STRIKE_UNIT, price_unit=price_unit)
    expiries = raw_quotes[qproc.EXPIRY_KEY].unique()
    pricing_errors = dict()
    for expiry in expiries:
        quotes_for_expiry = raw_quotes.loc[raw_quotes[qproc.EXPIRY_KEY] == expiry]
        strikes_for_quotes = quotes_for_expiry[qproc.STRIKE_KEY].values
        true_prices = quotes_for_expiry[qproc.MID_KEY].values

        vol_surface_prices = vol_surface.get_price(price_unit=price_unit, expiry=expiry,
                                                   strike=strikes_for_quotes, strike_unit=STRIKE_UNIT)
        errors = true_prices - vol_surface_prices
        pricing_errors_for_expiry = dict()
        for i in range(strikes_for_quotes.size):
            strike = strikes_for_quotes[i]
            pricing_errors_for_expiry[strike] = errors[i]

        pricing_errors[expiry] = pricing_errors_for_expiry

    if as_arr:
        return _get_pricing_errors_arr(pricing_errors)
    else:
        return pricing_errors


def _get_pricing_errors_arr(pricing_errors: dict) -> np.ndarray:
    pricing_errors_arr = []
    for t in pricing_errors.keys():
        pricing_errors_for_expiry = pricing_errors[t]
        pricing_errors_arr += [pricing_errors_for_expiry[k] for k in pricing_errors_for_expiry.keys()]

    return np.array(pricing_errors_arr)
