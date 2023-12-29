""" This module plots the bounds implied by the filtered option prices. """

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple

import qproc
from data import DataSetName, get_option_data


def main():
    option_data = get_option_data(DataSetName.example_data_afop)
    quote_processor = qproc.create_q_proc(option_prices=option_data.option_prices,
                                          price_unit=option_data.price_unit,
                                          strikes=option_data.strikes,
                                          expiries=option_data.expiries,
                                          forwards=option_data.forwards,
                                          rates=option_data.rates)

    quote_processor.filter(filter_type=qproc.FilterType.discard)

    price_unit = qproc.PriceUnit.normalized_call
    strike_unit = qproc.StrikeUnit.moneyness
    strike_range = (0.3, 2.0)  # moneyness
    create_bounds_plot(quote_processor=quote_processor,
                       strike_range=strike_range,
                       strike_unit=strike_unit,
                       price_unit=price_unit)


def create_bounds_plot(quote_processor: qproc.OptionQuoteProcessor,
                       strike_range: Tuple[float, float],
                       strike_unit: qproc.StrikeUnit,
                       price_unit: qproc.PriceUnit):

    strikes = np.linspace(start=strike_range[0], stop=strike_range[1], num=100)
    if strike_unit is qproc.StrikeUnit.log_moneyness:  # todo: modify
        strikes = np.log(strikes)

    quotes = quote_processor.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    expiries = quotes[qproc.EXPIRY_KEY].unique()
    for i in range(expiries.size):
        plt.figure()

        expiry = expiries[i]
        plt.title(f"$T = {expiry}$")

        lower_bounds = quote_processor.compute_lower_bound(expiry=expiry, strike=strikes, strike_unit=strike_unit,
                                                           price_unit=price_unit)
        plt.plot(strikes, lower_bounds, label='Lower bound', color='blue')

        upper_bounds = quote_processor.compute_upper_bound(expiry=expiry, strike=strikes, strike_unit=strike_unit,
                                                           price_unit=price_unit)
        plt.plot(strikes, upper_bounds, label='upper bound', color='red')

        quotes_for_expiry = quotes.loc[quotes[qproc.EXPIRY_KEY] == expiry]
        strikes_for_quotes = quotes_for_expiry[qproc.STRIKE_KEY]
        mid_prices = quotes_for_expiry[qproc.MID_KEY]
        plt.scatter(strikes_for_quotes, mid_prices, marker='o', color='black')

        plt.xlabel(strike_unit.name)
        plt.ylabel(price_unit.name)
        plt.legend()


if __name__ == "__main__":
    main()
    plt.show()
