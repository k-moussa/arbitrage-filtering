""" This module allows for plotting option price data. """

import matplotlib.pyplot as plt
import qproc
from data import DataSetName, get_option_data
from math import log


def main():
    option_data = get_option_data(DataSetName.dax_13_jun_2000)

    # rate_curve = qproc.create_rate_curve(option_data.unique_expiries(), zero_rates=option_data.rates)
    # test_zeros = [rate_curve.get_zero_rate(time=e) for e in option_data.unique_expiries()]
    # test_df = [-log(rate_curve.get_discount_factor(time=e))/e for e in option_data.unique_expiries()]

    quote_processor = qproc.create_q_proc(option_prices=option_data.option_prices,
                                          price_unit=option_data.price_unit,
                                          strikes=option_data.strikes,
                                          expiries=option_data.expiries,
                                          forwards=option_data.forwards,
                                          rates=option_data.rates)

    strike_unit = qproc.StrikeUnit.moneyness
    price_unit = qproc.PriceUnit.normalized_call
    # qproc.print_filter_errors(quote_processor=quote_processor,
    #                           strike_unit=strike_unit,
    #                           price_unit=price_unit,
    #                           filter_type=qproc.FilterType.strike,
    #                           smoothing_param=0.1)

    quote_processor.filter(filter_type=qproc.FilterType.expiry_forward)
    qproc.plot_quotes(quote_processor,
                      strike_unit=strike_unit,
                      price_unit=price_unit,
                      spt=qproc.SurfacePlotType.combined_2d,
                      points_else_lines=True)


if __name__ == "__main__":
    main()
    plt.show()
