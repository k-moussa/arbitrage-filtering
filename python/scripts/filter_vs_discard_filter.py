""" This module generates the results for the comparison of the arbitrage filter with the discard filter. """

import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
from typing import List, Optional, final

import qproc
import volsurface as vs 
from data import DataSetName, get_option_data

MAE_KEY: final = "MAE"
RMSE_KEY: final = "RMSE"


def main():
    option_data = get_option_data(DataSetName.dax_13_jun_2000)
    raw_data = qproc.create_q_proc(option_prices=option_data.option_prices,
                                   price_unit=option_data.price_unit,
                                   strikes=option_data.strikes,
                                   expiries=option_data.expiries,
                                   forwards=option_data.forwards,
                                   rates=option_data.rates,
                                   spot=option_data.spot)

    # The results from the discard filter may depend on the extrapolation method of the final points are discarded.
    extrapolation_param = 0.5
    price_unit = qproc.PriceUnit.vol
    smile_inter_types = [vs.InterpolationType.ncs, vs.InterpolationType.ccs, vs.InterpolationType.pmc,
                         vs.InterpolationType.pchip]
    print_pricing_errors(price_unit=price_unit, raw_data=raw_data, smile_inter_types=smile_inter_types,
                         filter_type=qproc.FilterType.discard, extrapolation_param=extrapolation_param)

    # The results only depend on the interpolation method when the discard filter is used
    smoothness_params = [0.01, 0.05, 0.1, 0.3, 0.5]
    for sm in smoothness_params:
        print_pricing_errors(price_unit=price_unit, raw_data=raw_data, smile_inter_types=[vs.InterpolationType.pchip],
                             filter_type=qproc.FilterType.strike, filter_smoothness_param=sm)

    create_plots(raw_data=raw_data, inter_type=vs.InterpolationType.pmc, smoothness_param=0.01,
                 extrapolation_param=extrapolation_param)
    
    
def print_pricing_errors(price_unit: qproc.PriceUnit, 
                         raw_data: qproc.OptionQuoteProcessor,
                         smile_inter_types: List[vs.InterpolationType],
                         filter_type: qproc.FilterType,
                         filter_smoothness_param: Optional[float] = None,
                         extrapolation_param: Optional[float] = None):

    aggregate_pricing_errors = get_aggregate_pricing_errors(
        price_unit=price_unit, raw_data=raw_data, smile_inter_types=smile_inter_types, filter_type=filter_type,
        filter_smoothness_param=filter_smoothness_param, extrapolation_param=extrapolation_param)

    formatted_output = "Method"
    if filter_smoothness_param is not None:
        formatted_output += f" ($\lambda = {filter_smoothness_param}$)"

    formatted_output += '\t&' + MAE_KEY + "\t&" + RMSE_KEY + "\n"
    for method_name in aggregate_pricing_errors.keys():
        results_for_method = aggregate_pricing_errors[method_name]
        incremental_output = method_name + '\t&' + f'{results_for_method[MAE_KEY]}' + '\t&' + \
            f'{results_for_method[RMSE_KEY]}'
        formatted_output += incremental_output + '\n'

    print(formatted_output)


def get_aggregate_pricing_errors(price_unit: qproc.PriceUnit,
                                 raw_data: qproc.OptionQuoteProcessor,
                                 smile_inter_types: List[vs.InterpolationType],
                                 filter_type: qproc.FilterType,
                                 filter_smoothness_param: Optional[float],
                                 extrapolation_param: Optional[float]) -> dict:
    """ Returns a nested dict (first by smile interpolation type, then by MAE / RMSE) with aggregate pricing errors. """

    aggregate_pricing_errors = dict()
    for sit in smile_inter_types:
        vol_surface = vs.create(smile_inter_type=sit, oqp=deepcopy(raw_data), filter_type=filter_type,
                                filter_smoothness_param=filter_smoothness_param,
                                extrapolation_param=extrapolation_param)
        vol_surface.calibrate()

        method_results = dict()
        method_results[MAE_KEY] = vs.compute_pricing_mae(quote_processor=raw_data, vol_surface=vol_surface,
                                                         price_unit=price_unit)
        method_results[RMSE_KEY] = vs.compute_pricing_rmse(quote_processor=raw_data, vol_surface=vol_surface,
                                                           price_unit=price_unit)

        method_key = get_method_name(inter_type=sit, filter_type=filter_type)
        aggregate_pricing_errors[method_key] = method_results

    return aggregate_pricing_errors


def get_method_name(inter_type: vs.InterpolationType,
                    filter_type: qproc.FilterType) -> str:

    return inter_type.name.upper() + " (" + filter_type.name + ")"


def create_plots(raw_data: qproc.OptionQuoteProcessor,
                 inter_type: vs.InterpolationType,
                 smoothness_param: float,
                 extrapolation_param: float):

    discard_vol_surface = vs.create(smile_inter_type=inter_type, oqp=deepcopy(raw_data),
                                    filter_type=qproc.FilterType.discard, extrapolation_param=extrapolation_param)
    discard_vol_surface.calibrate()

    filtered_vol_surface = vs.create(smile_inter_type=inter_type, oqp=deepcopy(raw_data),
                                     filter_type=qproc.FilterType.strike, filter_smoothness_param=smoothness_param,
                                     extrapolation_param=None)
    filtered_vol_surface.calibrate()

    plot_vol_smiles(raw_data=raw_data, discard_vol_surface=discard_vol_surface,
                    filtered_vol_surface=filtered_vol_surface, strike_unit=qproc.StrikeUnit.log_moneyness,
                    price_unit=qproc.PriceUnit.vol)
    plot_vol_smiles(raw_data=raw_data, discard_vol_surface=discard_vol_surface,
                    filtered_vol_surface=filtered_vol_surface, strike_unit=qproc.StrikeUnit.strike,
                    price_unit=qproc.PriceUnit.call)


def plot_vol_smiles(raw_data: qproc.OptionQuoteProcessor,
                    discard_vol_surface: vs.VolSurface,
                    filtered_vol_surface: vs.VolSurface,
                    strike_unit: qproc.StrikeUnit,
                    price_unit: qproc.PriceUnit):

    quotes = raw_data.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    expiries = quotes[qproc.EXPIRY_KEY].unique()
    for i in range(expiries.size):
        plt.figure()

        expiry = expiries[i]
        quotes_for_expiry = quotes.loc[quotes[qproc.EXPIRY_KEY] == expiry]
        strikes_for_quotes = quotes_for_expiry[qproc.STRIKE_KEY].values
        # plt.title(f"$T = {expiry}$")

        strikes = np.linspace(start=strikes_for_quotes[0], stop=strikes_for_quotes[-1], num=200)
        raw_prices = discard_vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=strikes,
                                               strike_unit=strike_unit)
        plt.plot(strikes, raw_prices, color='red', label='Discard filter')

        filtered_prices = filtered_vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=strikes,
                                                         strike_unit=strike_unit)
        plt.plot(strikes, filtered_prices, color='cornflowerblue', label='Arbitrage filter', ls='--')

        mid_prices = quotes_for_expiry[qproc.MID_KEY].values
        plt.scatter(strikes_for_quotes, mid_prices, marker='o', color='black', label='Quotes')

        plt.xlabel(strike_unit.name)
        plt.ylabel(price_unit.name)
        plt.legend()


if __name__ == "__main__":
    main()
    plt.show()
