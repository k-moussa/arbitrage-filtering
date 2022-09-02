''' Goal: This module generates plots the examples shown in "Arbitrage-Based Filtering of Option Price Data."

    Author: Karim Moussa (2017) '''


import matplotlib.pyplot as plt
import numpy as np
from scipy import interpolate
from copy import deepcopy
from math import exp, inf
from mpl_toolkits.mplot3d import Axes3D
from filter_implementation.quote_surface import QuoteSurface
from filter_implementation.convert_price_data \
    import data_to_quote_slice, strikes_vols_and_premia_to_quote_surface
from filter_implementation.volatility_functions \
    import discounted_black
from filter_implementation.filter_constants import \
    CALL_ONE_ELSE_PUT_MINUS_ONE, PROPER_RANDOM_SEED


def main():
    np.random.seed(PROPER_RANDOM_SEED)  # Fix the seed to keep same examples

    plot_strike_example_data()
    plot_strike_example_step_by_step()
    plot_strike_safeguard_example_data()
    plot_surface_example()
    plot_dax_data()
    # plot_dax_example_with_bounds()
    plot_option_implied_CDFs()
    # print_dax_data_latex()

    # max_strike = 3
    # max_expiry = 5
    # plot_example_data_surface(max_strike, max_expiry)
    #
    # expiries = [1/365, 7/365, 14/365, 31/365, 60/365, 90/365, 180/365, 1, 2, 5]
    # min_number_of_quotes_per_expiry = 5
    # max_number_of_quotes_per_expiry = 10
    #
    # quote_surface = create_random_surface_example_data(max_strike, expiries, min_number_of_quotes_per_expiry,
    #                                                    max_number_of_quotes_per_expiry)
    # plot_call_premia_for_quote_surface_moneyness(quote_surface)
    # quote_surface.filter_surface_forward(use_safeguard=True)
    # plot_call_premia_for_quote_surface_moneyness(quote_surface)


def surface_formula_example_data(strike, expiry):
    return max( (1 - 1/20*strike**2), 0.0)/(1.0 + expiry/20)


def plot_example_data_surface(max_strike, max_expiry, elements_per_slice = 20):
    fig = plt.figure()

    strike_range = np.linspace(0, max_strike, num=elements_per_slice)
    expiry_range = np.linspace(0, max_expiry, num = 20)
    strikes, expiries = np.meshgrid(strike_range, expiry_range)

    ax = Axes3D(fig)
    call_premia = np.zeros((len(strike_range), len(expiries)))


    for i in range(0, len(strikes)):
        for j in range(0, len(expiries)):
            call_premia[i,j] = surface_formula_example_data(strikes[i,j], expiries[i,j])

    ax.plot_surface(strikes, expiries, call_premia, rstride=1, cstride=1, cmap=plt.cm.coolwarm, linewidth=0,
                    antialiased=True)

    ax.set_xlabel("Strike")
    ax.set_ylabel("Expiry (years)")
    ax.set_zlabel("Call premium")


def create_random_surface_example_data(max_strike, expiries, min_number_of_quotes_per_expiry, max_number_of_quotes_per_expiry):
    number_of_expiries = len(expiries)
    strike_premium_lists = []

    for expiry in expiries:
        number_of_quotes =  np.random.random_integers(min_number_of_quotes_per_expiry, max_number_of_quotes_per_expiry) # 5
        strike_premium_list = []
        for i in range(0, number_of_quotes):
            strike = np.random.uniform(0.0, max_strike)
            call_premium = surface_formula_example_data(strike, expiry)
            strike_premium_list.append( (strike, call_premium) )

        strike_premium_lists.append(strike_premium_list)

    forwards = [1.0]*number_of_expiries
    discount_factors = [1.0]*number_of_expiries

    quote_surface = strikes_vols_and_premia_to_quote_surface(strike_premium_lists, expiries, forwards,
        discount_factors)

    return quote_surface


def plot_call_premia_for_quote_surface_moneyness(quote_surface):
    plt.figure()
    jet = plt.get_cmap('jet')
    colors = iter(jet(np.linspace(0, 1, 10)))

    for quote_slice in quote_surface.sorted_quote_slices:
        label_string = "T = {:}".format(quote_slice.expiry)
        plot_call_premiums_for_quote_slice(quote_slice, label_string, color=next(colors), strikes_else_moneyness=False )


def plot_implied_vols_for_quote_surface_moneyness(quote_surface):
    plt.figure()
    jet = plt.get_cmap('jet')
    colors = iter(jet(np.linspace(0, 1, 10)))

    for quote_slice in quote_surface.sorted_quote_slices:
        label_string = "T = {:}".format(quote_slice.expiry)
        plot_implied_vols_for_quote_slice(quote_slice, label_string, color=next(colors), strikes_else_moneyness=False )


def create_strike_example_data():
    expiry = 1
    forward = 1.0
    discount_factor = 1.0

    strike_list = [0.80*forward, 0.91*forward, forward, 1.10*forward, 1.22*forward]
    implied_vols = [0.40, 0.20, 0.15, 0.18, 0.30]

    call_premiums = [ discounted_black(forward, strike, implied_vol, expiry, discount_factor,
        CALL_ONE_ELSE_PUT_MINUS_ONE) for (strike, implied_vol) in zip(strike_list, implied_vols)]

    auxiliary_strike_list = strike_list[:]
    auxiliary_strike_list.insert(0, 0.0)

    auxiliary_call_premium_list = call_premiums[:]
    call_premium_at_strike_zero = discount_factor*forward
    auxiliary_call_premium_list.insert(0, call_premium_at_strike_zero)

    return strike_list, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, \
            expiry, forward, discount_factor


def plot_implied_vols_for_quote_slice(quote_slice, label_string = "", color = 'k', strikes_else_moneyness = True,
                                      marker="o"):
    if strikes_else_moneyness:
        domain = [quote.strike for quote in quote_slice.sorted_quote_list]
        plt.xlabel("$K$")
        # forward_string = "\t"*5 + "$(F(0,T) = $" + "{:.2f}".format(quote_slice.forward) + "$)$"
        # plt.xlabel("\t"*7 + "$K$ " + forward_string)
    else:
        domain = [quote.moneyness for quote in quote_slice.sorted_quote_list]
        plt.xlabel("$M$")

    implied_vols = [quote.implied_vol for quote in quote_slice.sorted_quote_list]
    plt.scatter(domain, implied_vols, color=color, label=label_string, marker = marker, s = 40.0)

    plt.ylabel("Implied volatility")
    plt.xlim([min(domain) - 0.01, max(domain) + 0.01])
    plt.ylim([0.0, max(implied_vols) * 1.5])
    plt.legend()


def plot_call_premiums_for_quote_slice(quote_slice, label_string = "", color = 'k', strikes_else_moneyness = True,
                                       marker = "o"):
    if strikes_else_moneyness:
        domain = [quote.strike for quote in quote_slice.sorted_quote_list]
        plt.xlabel("$K$")
        # forward_string = "\t"*5 + "$(F(0,T) = $" + "{:.2f}".format(quote_slice.forward) + "$)$"
        # plt.xlabel("\t"*7 + "$K$ " + forward_string)
    else:
        domain = [quote.moneyness for quote in quote_slice.sorted_quote_list]
        plt.xlabel("$M$")

    call_premiums = [quote.call_premium for quote in quote_slice.sorted_quote_list]

    plt.scatter(domain, call_premiums, color=color, label = label_string, marker = marker, s = 40.0)

    plt.ylabel("Call price")
    plt.xlim([min(domain) - 0.01, max(domain) + 0.01])
    plt.ylim([0.0, max(call_premiums) * 1.5])
    plt.legend()


def plot_original_and_filtered_quotes(quote_slice, use_safeguard = False):

    # plt.figure()
    plt.subplot(222)
    plot_call_premiums_for_quote_slice(quote_slice, label_string = "Original")

    plt.subplot(221)
    plot_implied_vols_for_quote_slice(quote_slice, label_string="Original")

    if use_safeguard:
        quote_slice.filter_in_strike_dimension_with_safeguard()
    else:
        quote_slice.filter_in_strike_dimension()

    plt.subplot(222)
    plot_call_premiums_for_quote_slice(quote_slice, label_string="Filtered", color = 'r', marker = "*")

    plt.subplot(221)
    plot_implied_vols_for_quote_slice(quote_slice, label_string="Filtered", color='r', marker = "*")


def plot_strike_example_data():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
        discount_factor = create_strike_example_data()

    plt.figure()
    plt.subplot(223)
    plt.scatter(auxiliary_strike_list, auxiliary_call_premium_list, color = 'k', label = "Original", s = 40.0)
    plt.plot(auxiliary_strike_list, auxiliary_call_premium_list, color = 'r')
    plt.xlabel("$K$")
    plt.ylabel("Call price")
    plt.xlim([min(auxiliary_strike_list) - 0.02, max(auxiliary_strike_list) + 0.02])
    plt.ylim([0.0, max(auxiliary_call_premium_list)+0.02])
    plt.legend()

    strike_vol_list = [ (strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice = data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor)
    plot_original_and_filtered_quotes(quote_slice)

    # plt.figure()

    plt.subplot(224)
    arbitrage_consistent_premium_set_postfilter = [quote.call_premium for quote in
        quote_slice.arbitrage_consistent_strike_sorted_set]
    plt.scatter(auxiliary_strike_list, arbitrage_consistent_premium_set_postfilter, color = 'k', label = "Filtered",
                s=40.0)
    plt.plot(auxiliary_strike_list, arbitrage_consistent_premium_set_postfilter)
    plt.xlabel("$K$")
    plt.ylabel("Call price")
    plt.xlim([min(auxiliary_strike_list) - 0.02, max(auxiliary_strike_list) + 0.02])
    plt.ylim([0.0, max(arbitrage_consistent_premium_set_postfilter)+0.02])
    plt.legend()


def plot_strike_example_step_by_step():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
    discount_factor = create_strike_example_data()
    strike_vol_list = [ (strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice = data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor)

    maximum_strike = max(strikes) * 1.1

    quote_slice.plot_filter_in_strike_dimension(maximum_strike)


def plot_original_and_filtered_quotes_and_safeguard_filter(quote_slice):
    quote_slice_copy = deepcopy(quote_slice)

    plt.subplot(212)
    plot_call_premiums_for_quote_slice(quote_slice, label_string = "Original")

    plt.subplot(211)
    plot_implied_vols_for_quote_slice(quote_slice, label_string="Original")

    quote_slice.filter_in_strike_dimension()

    plt.subplot(212)
    plot_call_premiums_for_quote_slice(quote_slice, label_string="Filtered", color = 'r', marker = "*")

    plt.subplot(211)
    plot_implied_vols_for_quote_slice(quote_slice, label_string="Filtered", color='r', marker = "*")

    quote_slice_copy.filter_in_strike_dimension_with_safeguard()

    plt.subplot(212)
    plot_call_premiums_for_quote_slice(quote_slice_copy, label_string="Filtered with safeguard", color = 'c', marker =
        "*")

    plt.subplot(211)
    plot_implied_vols_for_quote_slice(quote_slice_copy, label_string="Filtered with safeguard", color='c', marker = "*")

    plt.ylim(0.0, 0.4)
    plt.legend(loc = 0)


def create_strike_safeguard_example_data():
    expiry = 1
    forward = 1.0
    discount_factor = 1.0

    strike_list = [0.82*forward, 0.85*forward, 0.87*forward, 0.90*forward, 0.93*forward, 0.95*forward, 0.97*forward, forward,
                   1.04 * forward, 1.06*forward, 1.08 *forward, 1.10*forward, 1.12*forward, 1.15*forward, 1.19*forward]
    implied_vols = [0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.17, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20]

    call_premiums = [ discounted_black(forward, strike, implied_vol, expiry, discount_factor,
        CALL_ONE_ELSE_PUT_MINUS_ONE) for (strike, implied_vol) in zip(strike_list, implied_vols)]

    auxiliary_strike_list = strike_list[:]
    auxiliary_strike_list.insert(0, 0.0)

    auxiliary_call_premium_list = call_premiums[:]
    call_premium_at_strike_zero = discount_factor*forward
    auxiliary_call_premium_list.insert(0, call_premium_at_strike_zero)

    return strike_list, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, \
            expiry, forward, discount_factor


def plot_strike_safeguard_example_data():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
        discount_factor = create_strike_safeguard_example_data()

    plt.figure()
    strike_vol_list = [ (strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice = data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor)
    plot_original_and_filtered_quotes_and_safeguard_filter(quote_slice)


def plot_surface_example():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
    discount_factor = create_strike_example_data()
    strike_vol_list1 = [(strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice1 = data_to_quote_slice(strike_vol_list1, expiry, forward, discount_factor)

    implied_vols2 = [0.25, 0.20, 0.15, 0.13, 0.11]
    strike_vol_list2 = [(strike + 0.03*forward, 0.9*implied_vols2) for (strike, implied_vols2) in
                        zip(strikes, implied_vols2)]
    expiry2 = 2*expiry
    quote_slice2 = data_to_quote_slice(strike_vol_list2, expiry2, forward, discount_factor)

    quote_slices = [quote_slice1, quote_slice2]
    quote_surface = QuoteSurface(quote_slices)

    max_moneyness_slice1 = max([quote.moneyness for quote in quote_slice1.sorted_quote_list])
    max_moneyness_slice2 = max([quote.moneyness for quote in quote_slice2.sorted_quote_list])
    maximum_moneyness = max(max_moneyness_slice1, max_moneyness_slice2)*1.05

    quote_surface.plot_filter_in_expiry_dimension(maximum_moneyness)


def plot_original_and_filtered_quotes_dax(quote_slice):
    quote_slice_filtered = deepcopy(quote_slice)
    quote_slice_filtered.filter_in_strike_dimension()

    plt.figure()
    plt.subplot(311)
    plot_implied_vols_for_quote_slice(quote_slice, label_string = "Original")
    plot_implied_vols_for_quote_slice(quote_slice_filtered, label_string="Filtered", color = 'r', marker = "*")
    plt.xlim([2500,10100])
    plt.ylim([0,4])

    plt.subplot(312)
    plot_call_premiums_for_quote_slice(quote_slice, label_string = "Original")
    plot_call_premiums_for_quote_slice(quote_slice_filtered, label_string="Filtered", color = 'r', marker = "*")
    plt.xlim([2500,10100])
    plt.ylim([-100,6000])

    plt.subplot(313)
    plot_call_premiums_for_quote_slice(quote_slice, label_string = "Original")
    plot_call_premiums_for_quote_slice(quote_slice_filtered, label_string="Filtered", color = 'r', marker = "*")
    plt.xlim([7500,10050])
    plt.ylim([0,4])


def get_dax_data():
    """ Goal: this function loads the data, which is taken from the article "Arbitrage-free smoothing of the implied
              volatility surface" by Fengler (2009). """

    spot = 7268.91
    expiry = 3.0/365.0
    risk_free_rate = 4.36/100.0
    discount_factor = exp(-risk_free_rate*expiry)
    forward = 1.0/discount_factor*spot  # as dividend yield = 0

    strike_list = [2600,2800,3000,3200,3400,3600,3800,4000,4200,4400,4600,4800,4900,5000,5100,5200,5300,5400,5500,5600,
                   5700,5800,5900,6000,6100,6200,6250,6300,6350,6400,6450,6500,6550,6600,6650,6700,6750,6800,6850,6900,
                   6950,7000,7050,7100,7150,7200,7250,7300,7350,7400,7450,7500,7550,7600,7650,7700,7750,7800,7850,7900,
                   7950,8000,8050,8100,8150,8200,8250,8400,8600,8800,9000,9200,9400,9600,9800,10000]

    implied_vols = [3.6709,3.4092,3.1657,2.9381,2.7243,2.5228,2.3323,2.1516,1.9798,1.816,1.6596,1.5099,1.4373,1.3663,
                    1.2966,1.2283,1.1613,1.0956,1.0311,0.9678,0.9056,0.8445,0.7844,0.7254,0.6674,0.6103,0.5821,0.5542,
                    0.5264,0.5524,0.5288,0.5076,0.4808,0.4541,0.4277,0.4015,0.3755,0.3497,0.3414,0.3162,0.2971,0.2895,
                    0.2846,0.2685,0.2711,0.2556,0.253,0.2398,0.238,0.2359,0.2391,0.2487,0.2559,0.2696,0.2832,0.2903,
                    0.3025,0.3247,0.3469,0.3637,0.3567,0.3785,0.4002,0.4217,0.4431,0.4644,0.4855,0.5481,0.6297,0.7095,
                    0.7875,0.8637,0.9384,1.0114,1.0829,1.153]

    call_premiums = [ discounted_black(forward, strike, implied_vol, expiry, discount_factor,
        CALL_ONE_ELSE_PUT_MINUS_ONE) for (strike, implied_vol) in zip(strike_list, implied_vols)]

    auxiliary_strike_list = strike_list[:]
    auxiliary_strike_list.insert(0, 0.0)

    auxiliary_call_premium_list = call_premiums[:]
    call_premium_at_strike_zero = discount_factor*forward
    auxiliary_call_premium_list.insert(0, call_premium_at_strike_zero)

    return strike_list, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, \
            expiry, forward, discount_factor, spot


def plot_dax_data():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
    discount_factor, spot = get_dax_data()

    strike_vol_list = [ (strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice = data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor)
    plot_original_and_filtered_quotes_dax(quote_slice)


def compute_minimum_and_maximum_prices_for_strike_range(min_max_strike, quote_slice):
    min_strike = min_max_strike[0]
    max_strike = min_max_strike[1]

    min_price = inf
    max_price = 0.0

    for quote in quote_slice.sorted_quote_list:
        if min_strike <= quote.strike <= max_strike:
            min_price = min(min_price, quote.call_premium)
            max_price = max(max_price, quote.call_premium)

    return min_price, max_price


def plot_dax_example_with_bounds():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
    discount_factor, spot = get_dax_data()

    strike_vol_list = [ (strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice = data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor)

    original_quote_slice1 = deepcopy(quote_slice)
    original_quote_slice2 = deepcopy(quote_slice)

    min_strike = min(strikes) - 20
    max_strike = max(strikes)
    bound1 = 6900
    bound2 = 7600

    plt.figure()
    plt.subplot(311)
    strike_range1 = [min_strike, bound1]
    quote_slice.plot_strike_filter_dax_example(strike_range = strike_range1, ylim =
        compute_minimum_and_maximum_prices_for_strike_range( strike_range1, quote_slice), plot_expansion_factor_x = 1.001,
                                       plot_expansion_factor_y=1.075)

    plt.subplot(312)
    strike_range2 = [bound1, bound2]
    original_quote_slice1.plot_strike_filter_dax_example(strike_range = strike_range2, ylim =
            compute_minimum_and_maximum_prices_for_strike_range(strike_range2, original_quote_slice1),
                                                         plot_expansion_factor_x=1.0005, plot_expansion_factor_y=1.05)

    plt.subplot(313)
    strike_range3 = [bound2, max_strike]
    original_quote_slice2.plot_strike_filter_dax_example(strike_range = strike_range3, ylim =
        compute_minimum_and_maximum_prices_for_strike_range( strike_range3, original_quote_slice2),
        plot_expansion_factor_x = 1.003, plot_expansion_factor_y = 1.2)


def print_dax_data_latex():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
    discount_factor, spot = get_dax_data()

    strike_vol_list = [ (strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice = data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor)

    quote_slice.filter_in_strike_dimension()

    number_of_quotes = len(quote_slice.sorted_quote_list)
    number_of_filtered_quotes = 0

    print("K\t IV original\t IV filtered\t \% change\t C original\t C filtered\t \% change\t (K-F)/F\t is adjusted")

    for quote in quote_slice.sorted_quote_list:
        original_implied_vol = quote.implied_vol - quote.adjustment_implied_vol
        relative_adjustment_iv = quote.adjustment_implied_vol/original_implied_vol
        original_call_price = quote.call_premium - quote.adjustment_call_premium
        relative_adjustment_call_price = quote.adjustment_call_premium/original_call_price
        relative_moneyness = (quote.strike - quote_slice.forward) / forward * 100.0

        is_adjusted = "No"
        if quote.is_adjusted:
            is_adjusted = "Yes"

            italic_start = r"\textit{"
            italic_end = r"}" + "\t"

            italic_middle_IV = "{:.2f}".format(quote.implied_vol)
            italic_middle_Call_Price = "{:.2f}".format(quote.call_premium)

            italic_output_IV = italic_start + italic_middle_IV + italic_end
            italic_output_Call_Price = italic_start + italic_middle_Call_Price + italic_end

            print("{:.0f}\t{:.2f}\t".format(quote.strike, original_implied_vol) + italic_output_IV +
                  "{:.1f}\%\t".format(relative_adjustment_iv) + "{:.2f}\t".format(original_call_price) +
                  italic_output_Call_Price + "{:.1f}\%\t".format(relative_adjustment_call_price) +
                  "{:.1f}\%\t".format(relative_moneyness) + is_adjusted )
        else:
            print(("{:.0f}\t" + 2*"{:.2f}\t" + "{:.1f}" + "\%\t" + 2*"{:.2f}\t" + "{:.1f}" + "\%\t" +
                   "{:.1f}" + "\%\t" + is_adjusted).format(quote.strike, original_implied_vol, quote.implied_vol,
                    relative_adjustment_iv, original_call_price, quote.call_premium, relative_adjustment_call_price,
                                                 relative_moneyness) )

        if quote.is_adjusted:
            number_of_filtered_quotes += 1

    print("\nNumber of quotes: {:}".format(number_of_quotes) )
    print("Number of filtered quotes: {:} ({:.1f}%)".format(number_of_filtered_quotes, number_of_filtered_quotes/
                                                            number_of_quotes*100.0) )




def plot_CDF_for_quote_slice(quote_slice, number_of_points, plot_range, label, color = 'k'):
    strikes = [quote.strike for quote in quote_slice.sorted_quote_list]
    call_prices = [quote.call_premium for quote in quote_slice.sorted_quote_list]

    sorted_strikes, sorted_call_prices = zip(*sorted(zip(strikes, call_prices)))
    linear_interpolant = interpolate.interp1d(sorted_strikes, sorted_call_prices)

    minimum_strike = min(plot_range)
    maximum_strike = max(plot_range)

    strike_domain = np.linspace(minimum_strike, maximum_strike, num = number_of_points)
    interpolated_call_prices = linear_interpolant(strike_domain)

    option_implied_CDF = []
    discount_factor = quote_slice.discount_factor

    for i in range(0,number_of_points-1):
        difference_quotient = (interpolated_call_prices[i+1] - interpolated_call_prices[i] )/(strike_domain[i+1] -
                                                                                              strike_domain[i] )
        option_implied_CDF.append(1.0 + difference_quotient/discount_factor)

    plt.plot(strike_domain[:(-1)], option_implied_CDF, label = label, color = color)
    plt.xlim(plot_range)
    plt.xlabel("$S_T$")
    plt.ylabel("$\mathbb{Q}(S_T)$")
    plt.legend(loc = 0)


def plot_option_implied_CDFs():
    strikes, call_premiums, implied_vols, auxiliary_strike_list, auxiliary_call_premium_list, expiry, forward, \
    discount_factor, spot = get_dax_data()

    strike_vol_list = [ (strike, implied_vol) for (strike, implied_vol) in zip(strikes, implied_vols)]
    quote_slice = data_to_quote_slice(strike_vol_list, expiry, forward, discount_factor)

    filtered_quote_slice = deepcopy(quote_slice)
    filtered_quote_slice.filter_in_strike_dimension()

    number_of_points = 10000

    min_strike = min(strikes)
    max_strike = max(strikes)
    bound1 = 7000
    bound2 = 7600

    plt.figure()
    plt.subplot(221)
    strike_range1 = [min_strike, max_strike]
    plot_CDF_for_quote_slice(quote_slice, number_of_points, strike_range1, label = "Original", color = 'r')
    plot_CDF_for_quote_slice(filtered_quote_slice, number_of_points, strike_range1, label = "Filtered", color = 'b')

    plt.subplot(222)
    strike_range1 = [min_strike, bound1]
    plot_CDF_for_quote_slice(quote_slice, number_of_points, strike_range1, label = "Original", color = 'r')
    plot_CDF_for_quote_slice(filtered_quote_slice, number_of_points, strike_range1, label = "Filtered", color = 'b')

    plt.subplot(223)
    strike_range2 = [bound1, bound2]
    plot_CDF_for_quote_slice(quote_slice, number_of_points, strike_range2, label = "Original", color = 'r')
    plot_CDF_for_quote_slice(filtered_quote_slice, number_of_points, strike_range2, label = "Filtered", color = 'b')

    plt.subplot(224)
    strike_range3 = [bound2, max_strike]
    plot_CDF_for_quote_slice(quote_slice, number_of_points, strike_range3, label = "Original", color = 'r')
    plot_CDF_for_quote_slice(filtered_quote_slice, number_of_points, strike_range3, label = "Filtered", color = 'b')


if __name__ == "__main__":
    main()
    plt.show()
