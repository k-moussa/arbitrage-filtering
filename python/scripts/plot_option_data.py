""" This module allows for plotting option price data. """

import matplotlib.pyplot as plt
import qproc
from data import DataSetName, get_option_data


def main():
    option_data = get_option_data(DataSetName.spx500_5_feb_2018)
    quote_processor = qproc.create_q_proc(option_prices=option_data.option_prices,
                                          price_unit=option_data.price_unit,
                                          strikes=option_data.strikes,
                                          expiries=option_data.expiries,
                                          forwards=option_data.forwards,
                                          rates=option_data.rates)

    for price_unit in [qproc.PriceUnit.vol, qproc.PriceUnit.call]:
        plot_quotes(quote_processor, strike_trans=qproc.StrikeTransform.strike, price_unit=price_unit)


def plot_quotes(quote_processor: qproc.OptionQuoteProcessor,
                strike_trans: qproc.StrikeTransform,
                price_unit: qproc.PriceUnit):

    # todo: return a df instead
    quote_matrix = quote_processor.get_quote_matrix(strike_trans=strike_trans,
                                                    price_unit=price_unit)

    plt.figure()
    strikes = quote_matrix[:, qproc.STRIKE_INDEX]
    mid_prices = quote_matrix[:, qproc.MID_INDEX]
    plt.plot(strikes, mid_prices, marker='o')

    plt.xlabel(strike_trans.name)
    plt.ylabel(price_unit.name)


if __name__ == "__main__":
    main()
    plt.show()
