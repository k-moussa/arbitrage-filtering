""" This module plots the bounds implied by the filtered option prices. """

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple
from copy import deepcopy

import qproc
import volsurface
from data import DataSetName, get_option_data


def main():
    option_data = get_option_data(DataSetName.example_data_afop)
    raw_data = qproc.create_q_proc(option_prices=option_data.option_prices,
                                   price_unit=option_data.price_unit,
                                   strikes=option_data.strikes,
                                   expiries=option_data.expiries,
                                   forwards=option_data.forwards,
                                   rates=option_data.rates,
                                   spot=option_data.spot)

    vol_surface = volsurface.create(smile_inter_type=volsurface.InterpolationType.ncs,
                                    oqp=deepcopy(raw_data),
                                    filter_type=volsurface.FilterType.strike)

    price_unit = qproc.PriceUnit.normalized_call
    strike_unit = qproc.StrikeUnit.moneyness
    strike_range = (0.1, 3.0)
    plot_vol_surface(quote_processor=raw_data,
                     vol_surface=vol_surface,
                     strike_range=strike_range,
                     strike_unit=strike_unit,
                     price_unit=price_unit)


def plot_vol_surface(quote_processor: qproc.OptionQuoteProcessor,
                     vol_surface: volsurface.VolSurface,
                     strike_range: Tuple[float, float],
                     strike_unit: qproc.StrikeUnit,
                     price_unit: qproc.PriceUnit):

    vol_surface.calibrate()

    trans_strikes = np.linspace(start=strike_range[0], stop=strike_range[1], num=100)
    quotes = quote_processor.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    expiries = quotes[qproc.EXPIRY_KEY].unique()
    for i in range(expiries.size):
        plt.figure()

        expiry = expiries[i]
        plt.title(f"$T = {expiry}$")

        prices = vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=trans_strikes,
                                       strike_unit=strike_unit)
        plt.plot(trans_strikes, prices, color='red')

        quotes_for_expiry = quotes.loc[quotes[qproc.EXPIRY_KEY] == expiry]
        strikes_for_quotes = quotes_for_expiry[qproc.STRIKE_KEY]
        mid_prices = quotes_for_expiry[qproc.MID_KEY]
        plt.scatter(strikes_for_quotes, mid_prices, marker='o', color='black', label='Quotes')

        plt.xlabel(strike_unit.name)
        plt.ylabel(price_unit.name)
        plt.legend()


if __name__ == "__main__":
    main()
    plt.show()
