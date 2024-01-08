""" This module generates the results for the comparison of the arbitrage filter with direct interpolation of
    the raw data. """

import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy

import qproc
import volsurface
from data import DataSetName, get_option_data


def main():
    option_data = get_option_data(DataSetName.tsla_15_jun_2018)
    raw_data = qproc.create_q_proc(option_prices=option_data.option_prices,
                                   price_unit=option_data.price_unit,
                                   strikes=option_data.strikes,
                                   expiries=option_data.expiries,
                                   forwards=option_data.forwards,
                                   rates=option_data.rates,
                                   spot=option_data.spot)

    smile_inter_type = volsurface.InterpolationType.ncs
    raw_vol_surface = volsurface.create(smile_inter_type=smile_inter_type, oqp=deepcopy(raw_data), 
                                        filter_type=None, extrapolation_param=None)

    filtered_vol_surface = volsurface.create(smile_inter_type=smile_inter_type,
                                             oqp=deepcopy(raw_data), filter_type=volsurface.FilterType.strike, 
                                             filter_smoothness_param=0.01, extrapolation_param=None)

    create_plots(raw_data=raw_data, raw_vol_surface=raw_vol_surface,
                 filtered_vol_surface=filtered_vol_surface)


def create_plots(raw_data: qproc.OptionQuoteProcessor,
                 raw_vol_surface: volsurface.VolSurface,
                 filtered_vol_surface: volsurface.VolSurface):
    
    raw_vol_surface.calibrate()
    filtered_vol_surface.calibrate()
    plot_vol_smiles(raw_data=raw_data, raw_vol_surface=raw_vol_surface, filtered_vol_surface=filtered_vol_surface,
                    strike_unit=qproc.StrikeUnit.log_moneyness, price_unit=qproc.PriceUnit.vol)
    plot_vol_smiles(raw_data=raw_data, raw_vol_surface=raw_vol_surface, filtered_vol_surface=filtered_vol_surface,
                    strike_unit=qproc.StrikeUnit.strike, price_unit=qproc.PriceUnit.call)


def plot_vol_smiles(raw_data: qproc.OptionQuoteProcessor,
                    raw_vol_surface: volsurface.VolSurface,
                    filtered_vol_surface: volsurface.VolSurface,
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
        raw_prices = raw_vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=strikes, 
                                               strike_unit=strike_unit)
        plt.plot(strikes, raw_prices, color='red', label='No filter')
        
        filtered_prices = filtered_vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=strikes, 
                                                         strike_unit=strike_unit)
        plt.plot(strikes, filtered_prices, color='cornflowerblue', label='Arbitrage filter')

        mid_prices = quotes_for_expiry[qproc.MID_KEY].values
        plt.scatter(strikes_for_quotes, mid_prices, marker='o', color='black', label='Quotes')

        plt.xlabel(strike_unit.name)
        plt.ylabel(price_unit.name)
        plt.legend()


if __name__ == "__main__":
    main()
    plt.show()
