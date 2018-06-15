''' Goal: This module defines a QuoteSlice object used in the implementation of "Arbitrage-Based
             Filtering of Option Price Data."

    Author: Karim Moussa (2017) '''

import bisect
import numpy as np
import matplotlib.pyplot as plt
from math import inf
from copy import deepcopy
from numpy.random import shuffle

from .quote import Quote
from .filter_constants import DUMMY_FIELD_VALUE, ALPHA, PROPER_RANDOM_SEED, MAXIMUM_NUMBER_OF_ATTEMPTS, \
    MAXIMUM_PERCENTAGE_OF_QUOTES_ADJUSTED
from .sorting_algorithms import index, find_lt, find_gt


class QuoteSlice:
    def __init__(self, discount_factor, forward, expiry, quote_list):
        self.discount_factor = discount_factor
        self.forward = forward
        self.expiry = expiry

        self.sorted_quote_list = quote_list
        self.sorted_quote_list.sort(key=lambda x: x.ranking_quantity)

        self.quote0 = self.compute_quote0()
        self.arbitrage_consistent_strike_sorted_set = []

        self.is_filtered = False


    def compute_quote0(self):
        strike0 = 0.0
        dummy_implied_vol0 = DUMMY_FIELD_VALUE
        call_premium0 = self.discount_factor * self.forward
        dummy_ranking_quantity0 = DUMMY_FIELD_VALUE

        quote0 = Quote(strike0, self.expiry, dummy_implied_vol0, call_premium0, dummy_ranking_quantity0,
                       self.forward)
        return quote0


    def get_right_adjacent_quote(self, quote):
        return find_gt(self.arbitrage_consistent_strike_sorted_set, quote)


    def are_two_points_right_of_quote(self, quote):
        return self.arbitrage_consistent_strike_sorted_set[-2].strike > quote.strike


    def compute_right_difference_quotient(self, quote):
        if self.are_two_points_right_of_quote(quote):
            first_quote_to_right = self.get_right_adjacent_quote(quote)
            second_quote_to_right = self.get_right_adjacent_quote(first_quote_to_right)

            return (first_quote_to_right.call_premium - second_quote_to_right.call_premium)/ \
                   (first_quote_to_right.strike - second_quote_to_right.strike)
        else:
            return 0.0


    def is_enclosed_by_two_points(self, quote):
        return quote.strike < self.arbitrage_consistent_strike_sorted_set[-1].strike


    def are_two_points_left_of_quote(self, quote):
        return self.arbitrage_consistent_strike_sorted_set[1].strike < quote.strike


    def get_left_adjacent_quote(self, quote):
        return find_lt(self.arbitrage_consistent_strike_sorted_set, quote)


    def compute_left_difference_quotient(self, quote):
        if self.are_two_points_left_of_quote(quote):
            first_quote_to_left = self.get_left_adjacent_quote(quote)
            second_quote_to_left = self.get_left_adjacent_quote(first_quote_to_left)

            return (first_quote_to_left.call_premium - second_quote_to_left.call_premium)/\
                   (first_quote_to_left.strike - second_quote_to_left.strike)
        else:
            return -self.discount_factor


    def compute_lower_bound(self, quote):
        left_adjacent_quote = self.get_left_adjacent_quote(quote)
        left_difference_quotient = self.compute_left_difference_quotient(quote)
        lower_bound_from_left_difference_quotient = max(left_adjacent_quote.call_premium + left_difference_quotient * \
                                                   (quote.strike - left_adjacent_quote.strike), 0.0)

        if self.is_enclosed_by_two_points(quote):
            right_adjacent_quote = self.get_right_adjacent_quote(quote)
            right_difference_quotient = self.compute_right_difference_quotient(quote)
            lower_bound_from_right_difference_quotient = right_adjacent_quote.call_premium - right_difference_quotient* \
                (right_adjacent_quote.strike - quote.strike)

            return max(lower_bound_from_left_difference_quotient, lower_bound_from_right_difference_quotient)
        else:
            return lower_bound_from_left_difference_quotient


    def compute_upper_bound(self, quote):
        left_adjacent_quote = self.get_left_adjacent_quote(quote)

        if self.is_enclosed_by_two_points(quote):
            right_adjacent_quote = self.get_right_adjacent_quote(quote)

            interpolated_call_premium = ( (right_adjacent_quote.strike - quote.strike)*left_adjacent_quote.call_premium + \
                                        (quote.strike - left_adjacent_quote.strike) * right_adjacent_quote.call_premium )/ \
                                        (right_adjacent_quote.strike - left_adjacent_quote.strike)
            return interpolated_call_premium
        else:
            return left_adjacent_quote.call_premium


    def is_valid_quote(self, quote):
        lower_bound = self.compute_lower_bound(quote)
        upper_bound = self.compute_upper_bound(quote)

        return lower_bound <= quote.call_premium <= upper_bound


    def remove_quote_from_sorted_quote_list(self, quote):
        self.sorted_quote_list.remove(quote)


    def initial_fill_arbitrage_consistent_set(self):
        for quote in self.sorted_quote_list[:]:
            if self.is_valid_quote(quote):
                bisect.insort_left(self.arbitrage_consistent_strike_sorted_set, quote)
                self.remove_quote_from_sorted_quote_list(quote)


    def set_filtered_sorted_quote_list(self):
        self.sorted_quote_list = self.arbitrage_consistent_strike_sorted_set[:]
        self.sorted_quote_list.remove(self.quote0)


    def adjust_quote(self, quote, lower_bound, upper_bound):
        if quote.call_premium < lower_bound:
            new_premium = lower_bound + ALPHA * (upper_bound - lower_bound)
            quote.adjust(new_premium, self.forward, self.discount_factor)
        elif quote.call_premium > upper_bound:
            new_premium = lower_bound + (1.0 - ALPHA) * (upper_bound - lower_bound)
            quote.adjust(new_premium, self.forward, self.discount_factor)


    def fill_arbitrage_consistent_set_with_adjusted_quotes(self):
        for quote in self.sorted_quote_list:
            lower_bound = self.compute_lower_bound(quote)
            upper_bound = self.compute_upper_bound(quote)
            self.adjust_quote(quote, lower_bound, upper_bound)
            bisect.insort_left(self.arbitrage_consistent_strike_sorted_set, quote)


    def get_first_ranked_quote(self):
        return self.sorted_quote_list[0]


    def pop_first_ranked_quote(self):
        first_ranked_quote = self.get_first_ranked_quote()
        self.remove_quote_from_sorted_quote_list(first_ranked_quote)
        return first_ranked_quote


    def compute_theoretical_maximum_price(self):
        return self.quote0.call_premium


    def compute_theoretical_minimum_price(self, strike):
        return self.discount_factor * (max(self.forward - strike, 0.0))


    def truncate_European_call_theoretical_bounds(self, quote):
        # This function truncates a call premium based on the theoretical European call bounds
        theoretical_lower_bound = self.compute_theoretical_minimum_price(quote.strike)
        theoretical_upper_bound = self.compute_theoretical_maximum_price()

        self.adjust_quote(quote, theoretical_lower_bound, theoretical_upper_bound)


    def compute_initial_arbitrage_consistent_set(self):
        first_ranked_quote = self.pop_first_ranked_quote()
        self.truncate_European_call_theoretical_bounds(first_ranked_quote)
        return [self.quote0, first_ranked_quote]


    def filter_in_strike_dimension(self):
        self.arbitrage_consistent_strike_sorted_set = self.compute_initial_arbitrage_consistent_set()
        self.initial_fill_arbitrage_consistent_set()
        self.fill_arbitrage_consistent_set_with_adjusted_quotes()

        self.set_filtered_sorted_quote_list()
        self.is_filtered = True


    def compute_average_quote_adjustment(self, implied_vol_else_call = True):
        """ This function could be used to determine whether adjustments are acceptable."""

        total_adjustment = 0.0

        for quote in self.sorted_quote_list:
            total_adjustment += abs(quote.adjustment_implied_vol) if implied_vol_else_call else \
                abs(quote.adjustment_call_premium)

        average_adjustment = total_adjustment/len(self.sorted_quote_list)
        return average_adjustment


    def compute_percentage_of_quotes_adjusted(self):
        number_of_quotes_adjusted = 0

        for quote in self.sorted_quote_list:
            if quote.is_adjusted:
                number_of_quotes_adjusted += 1

        number_of_quotes = len(self.sorted_quote_list)
        percentage_of_quotes_adjusted = number_of_quotes_adjusted/number_of_quotes*100.0

        return percentage_of_quotes_adjusted


    def correct_arbitrage_consistent_set_postfilter(self):
        self.arbitrage_consistent_strike_sorted_set = self.sorted_quote_list[:]
        self.arbitrage_consistent_strike_sorted_set.sort(key=lambda x: x.strike)
        self.arbitrage_consistent_strike_sorted_set.insert(0, self.quote0)


    def filter_in_strike_dimension_with_safeguard(self):
        np.random.seed(PROPER_RANDOM_SEED)
        percentage_quotes_adjusted = inf
        adjustments_are_acceptable = False
        master_sorted_quotes = deepcopy(self.sorted_quote_list)

        for number_of_attempts in range(1,MAXIMUM_NUMBER_OF_ATTEMPTS + 1):
            self.filter_in_strike_dimension()
            new_percentage_quotes_adjusted = self.compute_percentage_of_quotes_adjusted()

            if new_percentage_quotes_adjusted < percentage_quotes_adjusted:
                percentage_quotes_adjusted = new_percentage_quotes_adjusted
                best_sorted_quote_list = self.sorted_quote_list
                adjustments_are_acceptable = percentage_quotes_adjusted <= MAXIMUM_PERCENTAGE_OF_QUOTES_ADJUSTED

            if adjustments_are_acceptable:
                break
            elif number_of_attempts < MAXIMUM_NUMBER_OF_ATTEMPTS:
                self.sorted_quote_list = deepcopy(master_sorted_quotes)
                partially_shuffled_copy = self.sorted_quote_list[1:]
                shuffle(partially_shuffled_copy)
                self.sorted_quote_list[1:] = partially_shuffled_copy

        self.sorted_quote_list = best_sorted_quote_list
        self.correct_arbitrage_consistent_set_postfilter()


    def create_dummy_quote_for_strike(self, strike):
        """ This function is used to enable re-using code that was used for computing the bounds for a certain quote
            (exploiting the overloading of the < and == operators for Quote objects) for computing bounds for a certain
             strike instead. """

        return Quote(strike, self.expiry, DUMMY_FIELD_VALUE, DUMMY_FIELD_VALUE, DUMMY_FIELD_VALUE, self.forward)


    def compute_bound_for_moneyness(self, moneyness, bound_side):
        """ This function enables requesting the bounds for a strike that corresponds to a quote in the
            arbitrage consistent set, and is to be used only in the forward surface filter procedure. """

        strike = moneyness * self.forward
        dummy_quote_for_strike = self.create_dummy_quote_for_strike(strike)

        index_for_strike = index(self.arbitrage_consistent_strike_sorted_set, dummy_quote_for_strike)
        strike_in_arbitrage_consistent_set = index_for_strike != -1

        if strike_in_arbitrage_consistent_set:
            return self.arbitrage_consistent_strike_sorted_set[index_for_strike].call_premium
        else:
            if bound_side == "lower":
                return self.compute_lower_bound(dummy_quote_for_strike)
            elif bound_side == "upper":
                return self.compute_upper_bound(dummy_quote_for_strike)


    def compute_lower_bound_for_moneyness(self, moneyness):
        ''' This function is used for filtering in the expiry dimension '''

        return self.compute_bound_for_moneyness(moneyness, bound_side = "lower")


    def compute_upper_bound_for_moneyness(self, moneyness):
        ''' This function is used for filtering in the expiry dimension'''

        return self.compute_bound_for_moneyness(moneyness, bound_side = "upper")


    def set_quotes_to_maximum_theoretical_value(self):
        maximum_call_price = self.compute_theoretical_maximum_price()
        for quote in self.sorted_quote_list:
            quote.adjust(maximum_call_price, self.forward, self.discount_factor)


    def final_safeguard_attempt_surface(self):
        self.set_quotes_to_maximum_theoretical_value()
        self.correct_arbitrage_consistent_set_postfilter()


    """ ##################### Plot functions ##################### """

    def compute_bounds_for_strike_plot_version(self, strike):
        a = self.arbitrage_consistent_strike_sorted_set

        if any(quote.strike == strike for quote in a):
            quote = next(quote for quote in a if quote.strike == strike)
            return (quote.call_premium, quote.call_premium)
        else:  # strike not in arbitrage-consistent set
            dummy_quote_for_strike = self.create_dummy_quote_for_strike(strike)
            lower_bound = self.compute_lower_bound(dummy_quote_for_strike)
            upper_bound = self.compute_upper_bound(dummy_quote_for_strike)
            return lower_bound, upper_bound


    def plot_bounds_for_strikes(self, strikes):
        lower_bounds = []
        upper_bounds = []

        for strike in strikes:
            lower_bound, upper_bound = self.compute_bounds_for_strike_plot_version(strike)
            lower_bounds.append(lower_bound)
            upper_bounds.append(upper_bound)

        plt.plot(strikes, lower_bounds, label = "Lower bound", color = "b")
        plt.plot(strikes, upper_bounds, label="Upper bound", color="r")


    def set_plot_parameters(self, max_strike, max_price):
        plt.legend(loc=0, prop={'size': 12})
        plt.xlabel("$K$")
        plt.ylabel("Call price")
        plt.xlim(-0.02, max_strike)
        plt.ylim(-0.01, max_price + 0.02)


    def plot_arbitrage_consistent_set_and_bounds(self, strikes, subplot_index, s = 40):
        a = self.arbitrage_consistent_strike_sorted_set

        plt.subplot(3, 3, subplot_index)
        self.plot_bounds_for_strikes(strikes)
        plt.scatter([quote.strike for quote in a], [quote.call_premium for quote in a], color = 'k',
                    label="$\mathbb{A}$", s = s)


    def plot_original_data_and_theoretical_call_bounds(self, strikes, maximum_strike, subplot = True,
                                                       plot_theoretical_call_bounds = True, s = 40):
        original_strikes = [quote.strike for quote in self.sorted_quote_list]
        original_strikes.insert(0, self.quote0.strike)

        original_call_prices = [quote.call_premium for quote in self.sorted_quote_list]
        original_call_prices.insert(0, self.quote0.call_premium)

        if subplot:
            plt.subplot(3, 3, 1)

        plt.scatter(original_strikes, original_call_prices, color = 'k', label="Original data", s = s)

        if plot_theoretical_call_bounds:
            lower_bounds = [self.compute_theoretical_minimum_price(strike) for strike in strikes ]
            num_elements = len(strikes)
            upper_bounds = [self.compute_theoretical_maximum_price()]*num_elements

            plt.plot(strikes, lower_bounds, label = "Lower bound", color = "b")
            plt.plot(strikes, upper_bounds, label= "Upper bound", color="r")
        self.set_plot_parameters(maximum_strike, self.quote0.call_premium)


    def plot_filter_in_strike_dimension(self, maximum_strike, s = 40):
        plt.figure()

        strikes = np.linspace(0.0, maximum_strike, num = 10000)
        self.plot_original_data_and_theoretical_call_bounds(strikes, maximum_strike, s = s)

        self.arbitrage_consistent_strike_sorted_set = self.compute_initial_arbitrage_consistent_set()

        self.plot_arbitrage_consistent_set_and_bounds(strikes, subplot_index = 2)
        self.set_plot_parameters(maximum_strike, self.quote0.call_premium)
        subplot_index = 3

        a = self.arbitrage_consistent_strike_sorted_set

        # initial fill of arbitrage consistent_set
        for quote in self.sorted_quote_list[:]:
            self.plot_arbitrage_consistent_set_and_bounds(strikes, subplot_index)
            plt.scatter(quote.strike, quote.call_premium, label="New quote", color="g", s = s)
            self.set_plot_parameters(max(strikes), self.quote0.call_premium)
            subplot_index += 1

            if self.is_valid_quote(quote):
                bisect.insort_left(self.arbitrage_consistent_strike_sorted_set, quote)
                self.remove_quote_from_sorted_quote_list(quote)

        # fill arbitrage consistent set with adjusted quotes
        for quote in self.sorted_quote_list:
            self.plot_arbitrage_consistent_set_and_bounds(strikes, subplot_index)
            plt.scatter(quote.strike, quote.call_premium, label="New quote", color="g", s = s)

            lower_bound = self.compute_lower_bound(quote)
            upper_bound = self.compute_upper_bound(quote)
            self.adjust_quote(quote, lower_bound, upper_bound)
            bisect.insort_left(self.arbitrage_consistent_strike_sorted_set, quote)

            plt.scatter(quote.strike, quote.call_premium, label="Adjusted quote", color="r", s = s)
            self.set_plot_parameters(max(strikes), self.quote0.call_premium)
            subplot_index += 1

        self.plot_arbitrage_consistent_set_and_bounds(strikes, subplot_index)
        self.set_plot_parameters(max(strikes), self.quote0.call_premium)

        self.set_filtered_sorted_quote_list()
        self.is_filtered = True


    def plot_original_data(self):
        original_strikes = [quote.strike for quote in self.sorted_quote_list]

        original_call_prices = [quote.call_premium for quote in self.sorted_quote_list]
        plt.scatter(original_strikes, original_call_prices, color = 'k', label="Original data")


    def plot_strike_filter_dax_example(self, strike_range, ylim, plot_expansion_factor_x = 1.0,
                                       plot_expansion_factor_y=1.0):
        strikes = np.linspace(strike_range[0]/plot_expansion_factor_x, strike_range[1]*plot_expansion_factor_x,
                              num = 10000)
        self.plot_original_data_and_theoretical_call_bounds(strikes, strike_range[1], subplot = False,
                                                            plot_theoretical_call_bounds=False)
        self.arbitrage_consistent_strike_sorted_set = self.compute_initial_arbitrage_consistent_set()
        a = self.arbitrage_consistent_strike_sorted_set

        no_rejections = True

        # initial fill of arbitrage consistent_set
        for quote in self.sorted_quote_list[:]:

            if self.is_valid_quote(quote):
                bisect.insort_left(self.arbitrage_consistent_strike_sorted_set, quote)
                self.remove_quote_from_sorted_quote_list(quote)
            elif no_rejections:
                print("Number of accepted quotes before first rejected quote = {:.0f}".format(len(a) - 1) )
                no_rejections = False

        self.plot_bounds_for_strikes(strikes)
        plt.scatter([quote.strike for quote in a], [quote.call_premium for quote in a], color='c',
            label="$\mathbb{A}$")

        plt.legend(loc=0, prop={'size': 14})
        plt.xlabel("$K$")
        plt.ylabel("Call price")

        plt.xlim(strike_range[0]/plot_expansion_factor_x, strike_range[1]*plot_expansion_factor_x)
        plt.ylim(ylim[0]/plot_expansion_factor_y, ylim[1]*plot_expansion_factor_y)


    """ ##################### End of plot functions ##################### """