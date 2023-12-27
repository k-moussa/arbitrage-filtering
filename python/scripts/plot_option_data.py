""" This module allows for plotting option price data. """

import matplotlib.pyplot as plt
import qproc
from data import DataSetName, get_option_data


def main():
    option_data = get_option_data(DataSetName.example_data_afop)
    quote_processor = qproc.create_q_proc(option_prices=option_data.option_prices,
                                          price_unit=option_data.price_unit,
                                          strikes=option_data.strikes,
                                          expiries=option_data.expiries,
                                          forwards=option_data.forwards,
                                          rates=option_data.rates,
                                          filter_type=qproc.FilterType.strike)

    for price_unit in [qproc.PriceUnit.call]: #[qproc.PriceUnit.vol, qproc.PriceUnit.call, qproc.PriceUnit.normalized_call]:
        plot_quotes(quote_processor, strike_unit=qproc.StrikeUnit.strike, price_unit=price_unit)


def plot_quotes(quote_processor: qproc.OptionQuoteProcessor,
                strike_unit: qproc.StrikeUnit,
                price_unit: qproc.PriceUnit):

    quotes = quote_processor.get_quotes(strike_unit=strike_unit, price_unit=price_unit)
    expiries = quotes[qproc.EXPIRY_KEY].unique()
    for i in range(expiries.size):
        plt.figure()

        expiry = expiries[i]
        quotes_for_expiry = quotes.loc[quotes[qproc.EXPIRY_KEY] == expiry]
        strikes = quotes_for_expiry[qproc.STRIKE_KEY]
        mid_prices = quotes_for_expiry[qproc.MID_KEY]
        plt.plot(strikes, mid_prices, marker='o')

        plt.title(f"$T = {expiry}$")
        plt.xlabel(strike_unit.name)
        plt.ylabel(price_unit.name)


if __name__ == "__main__":
    main()
    plt.show()
