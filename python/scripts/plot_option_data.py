""" This module allows for plotting option price data. """

import matplotlib.pyplot as plt
import qproc
from data import DataSetName, get_option_data


def main():
    option_data = get_option_data(DataSetName.dax_13_jun_2000_3days)
    quote_processor = qproc.create_q_proc(option_prices=option_data.option_prices,
                                          price_unit=option_data.price_unit,
                                          strikes=option_data.strikes,
                                          expiries=option_data.expiries,
                                          forwards=option_data.forwards,
                                          rates=option_data.rates,
                                          spot=option_data.spot)

    strike_unit = qproc.StrikeUnit.strike
    price_unit = qproc.PriceUnit.vol
    # qproc.print_filter_errors(quote_processor=quote_processor,
    #                           strike_unit=strike_unit,
    #                           price_unit=price_unit,
    #                           filter_type=qproc.FilterType.strike,
    #                           smoothing_param=0.1)

    quote_processor.filter(filter_type=qproc.FilterType.strike)
    qproc.plot_quotes(quote_processor,
                      strike_unit=strike_unit,
                      price_unit=price_unit,
                      spt=qproc.SurfacePlotType.combined_2d,
                      points_else_lines=True)


if __name__ == "__main__":
    main()
    plt.show()
