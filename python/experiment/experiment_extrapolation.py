""" This scripts generates the results for the extrapolation illustration. """

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

    price_unit = qproc.PriceUnit.vol  #qproc.PriceUnit.vol
    strike_unit = qproc.StrikeUnit.moneyness  # qproc.StrikeUnit.log_moneyness
    strike_range = (1, 4)  # (-7.0, 7.0)
    plot_vol_surface(raw_data=raw_data,
                     strike_range=strike_range,
                     strike_unit=strike_unit,
                     price_unit=price_unit,
                     smile_inter_type=volsurface.InterpolationType.pchip,
                     filter_type=volsurface.FilterType.strike,
                     smoothness_param=0.01)


def plot_vol_surface(raw_data: qproc.OptionQuoteProcessor,
                     strike_range: Tuple[float, float],
                     strike_unit: qproc.StrikeUnit,
                     price_unit: qproc.PriceUnit,
                     smile_inter_type: volsurface.InterpolationType,
                     filter_type: volsurface.FilterType,
                     smoothness_param: float):

    oqp = deepcopy(raw_data)
    oqp.filter(filter_type=filter_type, smoothing_param=smoothness_param)
    vol_surface = volsurface.create(smile_inter_type=smile_inter_type,
                                    oqp=deepcopy(raw_data),
                                    filter_type=filter_type,
                                    filter_smoothness_param=smoothness_param)
    vol_surface.calibrate()

    trans_strikes = np.linspace(start=strike_range[0], stop=strike_range[1], num=100)
    quotes = raw_data.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    expiries = quotes[qproc.EXPIRY_KEY].unique()
    for i in range(expiries.size):
        plt.figure()

        expiry = expiries[i]
        plt.title(f"$T = {expiry}$")

        lower_bounds = oqp.compute_lower_bound(expiry=expiry, strike=trans_strikes, strike_unit=strike_unit,
                                               price_unit=price_unit)
        plt.plot(trans_strikes, lower_bounds, label='Lower bound', color='blue')

        upper_bounds = oqp.compute_upper_bound(expiry=expiry, strike=trans_strikes, strike_unit=strike_unit,
                                               price_unit=price_unit)
        plt.plot(trans_strikes, upper_bounds, label='Upper bound', color='red')

        prices = vol_surface.get_price(price_unit=price_unit, expiry=expiry, strike=trans_strikes,
                                       strike_unit=strike_unit)
        plt.plot(trans_strikes, prices, color='green', label='Interpolation')

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
