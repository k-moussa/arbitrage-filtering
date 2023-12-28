""" This module allows for printing quotes in terms of a chosen strike and price unit. """

import numpy as np
from copy import deepcopy
from .globals import *


def print_filter_errors(quote_processor: OptionQuoteProcessor,
                        strike_unit: StrikeUnit,
                        price_unit: PriceUnit,
                        filter_type: FilterType,
                        smoothing_param: Optional[float] = DEFAULT_SMOOTHING_PARAM,
                        param_grid: Tuple[float] = DEFAULT_SMOOTHING_PARAM_GRID):

    quote_processor = deepcopy(quote_processor)

    if filter_type is FilterType.discard:
        raise RuntimeError("filter errors cannot be determined for discard version.")

    quotes_raw = quote_processor.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    quote_processor.filter(filter_type, smoothing_param=smoothing_param, param_grid=param_grid)
    quotes_filtered = quote_processor.get_quotes(strike_unit=strike_unit, price_unit=price_unit)

    true_values = quotes_raw[MID_KEY].values
    diffs = true_values - quotes_filtered[MID_KEY].values

    print("Mean " + price_unit.name, np.mean(true_values))

    mae = np.mean(np.abs(diffs))
    print("MAE = ", mae)

    rmse = np.sqrt(np.mean(diffs**2))
    print("RMSE = ", rmse)
