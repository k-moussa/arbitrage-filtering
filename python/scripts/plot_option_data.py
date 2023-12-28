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
        qproc.plot_quotes(quote_processor, strike_unit=qproc.StrikeUnit.strike, price_unit=price_unit,
                          spt=qproc.SurfacePlotType.combined_2d, points_else_lines=True)


if __name__ == "__main__":
    main()
    plt.show()
