""" This module allows for plotting quotes in terms of a chosen strike and price unit. """

import matplotlib.pyplot as plt
from .globals import *


def plot_quotes(quote_processor: OptionQuoteProcessor,
                strike_unit: StrikeUnit,
                price_unit: PriceUnit,
                spt: SurfacePlotType,
                points_else_lines: bool = True):

    plt.figure()
    plot_func = plt.scatter if points_else_lines else plt.plot

    quotes = quote_processor.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    expiries = quotes[EXPIRY_KEY].unique()
    for i in range(expiries.size):
        expiry = expiries[i]

        if spt is SurfacePlotType.separate:
            if i > 0:
                plt.figure()

            plt.title(f"$T = {expiry}$")
            label = None
        elif spt is SurfacePlotType.combined_2d:
            label = f"$T = {expiry}$"
        else:
            raise RuntimeError(f"Unhandled spt {spt.name}.")

        quotes_for_expiry = quotes.loc[quotes[EXPIRY_KEY] == expiry]
        strikes = quotes_for_expiry[STRIKE_KEY]
        mid_prices = quotes_for_expiry[MID_KEY]
        plot_func(strikes, mid_prices, marker='o', label=label)

        plt.xlabel(strike_unit.name)
        plt.ylabel(price_unit.name)

    if spt is SurfacePlotType.combined_2d:
        plt.legend()
