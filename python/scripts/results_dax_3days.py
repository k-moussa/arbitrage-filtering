""" This module generates the results for the DAX data set with 3 days expiry. """

import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
from typing import Optional, Tuple, final

import qproc
import volsurface
from data import DataSetName, get_option_data
from scripts.filter_vs_discard_filter import print_pricing_errors
import volsurface as vs

FILTER_SMOOTHNESS_PARAM: final = 0.0
SMILE_INTER_TYPE = volsurface.InterpolationType.linear


def main():
    option_data = get_option_data(DataSetName.dax_13_jun_2000_3days)
    raw_data = qproc.create_q_proc(option_prices=option_data.option_prices,
                                   price_unit=option_data.price_unit,
                                   strikes=option_data.strikes,
                                   expiries=option_data.expiries,
                                   forwards=option_data.forwards,
                                   rates=option_data.rates,
                                   spot=option_data.spot)

    # for xlim in [None]:
    #     raw_vol_surface = volsurface.create(smile_inter_type=SMILE_INTER_TYPE, oqp=deepcopy(raw_data),
    #                                         filter_type=None, extrapolation_param=None)
    #
    #     filtered_vol_surface = volsurface.create(smile_inter_type=SMILE_INTER_TYPE,
    #                                              oqp=deepcopy(raw_data), filter_type=volsurface.FilterType.strike,
    #                                              filter_smoothness_param=FILTER_SMOOTHNESS_PARAM,
    #                                              extrapolation_param=None)
    #
    #     create_plots(raw_data=raw_data, raw_vol_surface=raw_vol_surface,
    #                  filtered_vol_surface=filtered_vol_surface, xlim=xlim)

    print_pricing_errors(price_unit=qproc.PriceUnit.vol, raw_data=raw_data,
                         smile_inter_types=[SMILE_INTER_TYPE],
                         filter_type=qproc.FilterType.strike, filter_smoothness_param=FILTER_SMOOTHNESS_PARAM)


def create_plots(raw_data: qproc.OptionQuoteProcessor,
                 raw_vol_surface: volsurface.VolSurface,
                 filtered_vol_surface: volsurface.VolSurface,
                 xlim: Optional[Tuple[float, float]] = None):
    
    raw_vol_surface.calibrate()
    filtered_vol_surface.calibrate()
    plot_vol_smiles(raw_data=raw_data, raw_vol_surface=raw_vol_surface, filtered_vol_surface=filtered_vol_surface,
                    strike_unit=qproc.StrikeUnit.strike, price_unit=qproc.PriceUnit.vol, xlim=xlim)

    plot_risk_neutral_cdf(raw_data=raw_data, raw_vol_surface=raw_vol_surface,
                          filtered_vol_surface=filtered_vol_surface, xlim=xlim)


def plot_vol_smiles(raw_data: qproc.OptionQuoteProcessor,
                    raw_vol_surface: volsurface.VolSurface,
                    filtered_vol_surface: volsurface.VolSurface,
                    strike_unit: qproc.StrikeUnit,
                    price_unit: qproc.PriceUnit,
                    xlim: Optional[Tuple[float, float]]):

    quotes = raw_data.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    expiries = quotes[qproc.EXPIRY_KEY].unique()
    for i in [0]: #range(expiries.size):
        plt.figure()

        expiry = expiries[i]
        quotes_for_expiry = quotes.loc[quotes[qproc.EXPIRY_KEY] == expiry]
        strikes_for_quotes = quotes_for_expiry[qproc.STRIKE_KEY].values
        # plt.title(f"$T = {expiry}$")

        strikes = np.linspace(start=strikes_for_quotes[0], stop=strikes_for_quotes[-1], num=200)
        raw_prices = raw_vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=strikes, 
                                               strike_unit=strike_unit)
        plt.plot(strikes, raw_prices, color='red', label='No filter')
        
        filtered_prices = filtered_vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=strikes,
                                                         strike_unit=strike_unit)
        plt.plot(strikes, filtered_prices, color='cornflowerblue', label='Arbitrage filter', ls='--')

        mid_prices = quotes_for_expiry[qproc.MID_KEY].values
        plt.scatter(strikes_for_quotes, mid_prices, marker='o', color='black', label='Quotes')

        plt.xlabel(strike_unit.name)
        plt.ylabel(price_unit.name)
        plt.legend()
        plt.xlim(xlim)


def plot_risk_neutral_cdf(raw_data: qproc.OptionQuoteProcessor,
                          raw_vol_surface: volsurface.VolSurface,
                          filtered_vol_surface: volsurface.VolSurface,
                          xlim: Optional[Tuple[float, float]]):

    quotes = raw_data.get_quotes(strike_unit=qproc.StrikeUnit.strike, price_unit=qproc.PriceUnit.call)
    expiries = quotes[qproc.EXPIRY_KEY].unique()
    for i in [0]: #range(expiries.size):
        plt.figure()

        expiry = expiries[i]
        quotes_for_expiry = quotes.loc[quotes[qproc.EXPIRY_KEY] == expiry]
        strikes_for_quotes = quotes_for_expiry[qproc.STRIKE_KEY].values
        x = np.linspace(start=strikes_for_quotes[0] * 1.01, stop=strikes_for_quotes[-1] / 1.01, num=500)

        raw_density = raw_vol_surface.compute_risk_neutral_cdf(expiry=expiry, x=x)
        plt.plot(x, raw_density, color='red', label='No filter')

        filtered_density = filtered_vol_surface.compute_risk_neutral_cdf(expiry=expiry, x=x)
        plt.plot(x, filtered_density, color='cornflowerblue', label='Arbitrage filter', ls='--')

        plt.xlabel('$S_T$')
        plt.ylabel('$q(S_T)$', rotation=0)
        plt.legend()
        plt.xlim(xlim)

if __name__ == "__main__":
    main()
    plt.show()
