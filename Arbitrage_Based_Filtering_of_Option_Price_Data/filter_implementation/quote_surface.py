''' Goal: This module defines a QuoteSurface object used in the implementation of "Arbitrage-Based
             Filtering of Option Price Data."

    Author: Karim Moussa (2017) '''


import bisect
import numpy as np
import matplotlib.pyplot as plt
from math import inf
from copy import deepcopy
from numpy.random import shuffle

from .filter_exceptions import LowerBoundMoneynessTooHighException, PreviousPremiumTooHighException
from .filter_constants import MAXIMUM_NUMBER_OF_ATTEMPTS, MAXIMUM_NUMBER_OF_FAILED_ATTEMPTS, PROPER_RANDOM_SEED, \
    MAXIMUM_PERCENTAGE_OF_QUOTES_ADJUSTED


class QuoteSurface:
    def __init__(self, quote_slices):
        """ Inputs: quote_slices: a list of QuoteSlice objects for different time to expiries """

        self.sorted_quote_slices = quote_slices
        self.sorted_quote_slices.sort(key=lambda slice: slice.expiry)
        self.number_of_slices = len(self.sorted_quote_slices)
        self.is_filtered = False
        self.filtered_slices_indices = []


    def compute_scaling_factor_upper_bound_this_expiry(self, quote_slice_T1, quote_slice_T2):
        return 1.0/self.compute_scaling_factor_expiry_lower_bound(quote_slice_T1, quote_slice_T2)


    def previous_premium_exceeds_upper_bound(self, quote_slice):
        for index in self.filtered_slices_indices:
            previously_filtered_quote_slice = self.sorted_quote_slices[index]
            for quote in previously_filtered_quote_slice.sorted_quote_list:
                if quote.call_premium > self.compute_scaling_factor_upper_bound_this_expiry(
                        previously_filtered_quote_slice, quote_slice)*\
                        quote_slice.compute_upper_bound_for_moneyness(quote.moneyness):
                    return True

        return False


    def adjust_quote_forward_filtering(self, quote, quote_slice):
        lower_bound, upper_bound = self.compute_bounds_forward_filter(quote, quote_slice)
        quote_slice.adjust_quote(quote, lower_bound, upper_bound)


    def fill_arbitrage_consistent_set_with_adjusted_quotes_surface_forward(self, quote_slice):
        for quote in quote_slice.sorted_quote_list:
            self.adjust_quote_forward_filtering(quote, quote_slice)
            bisect.insort_left(quote_slice.arbitrage_consistent_strike_sorted_set, quote)


    def compute_bounds_forward_filter(self, quote, quote_slice):
        lower_bound_this_expiry = quote_slice.compute_lower_bound(quote)
        lower_bound_implied_by_filtered_slices = self.compute_infimum_for_moneyness_filtered_slices(quote.moneyness,
                                                                                                    quote_slice)
        lower_bound = max(lower_bound_this_expiry, lower_bound_implied_by_filtered_slices)
        upper_bound = quote_slice.compute_upper_bound(quote)

        if lower_bound_implied_by_filtered_slices > upper_bound:
            raise LowerBoundMoneynessTooHighException

        return lower_bound, upper_bound


    def is_valid_quote_forward_filtering(self, quote, quote_slice):
        lower_bound, upper_bound = self.compute_bounds_forward_filter(quote, quote_slice)
        return lower_bound <= quote.call_premium <= upper_bound


    def initial_fill_arbitrage_consistent_set_forward(self, quote_slice):
        for quote in quote_slice.sorted_quote_list[:]:
            if self.is_valid_quote_forward_filtering(quote, quote_slice):
                bisect.insort_left(quote_slice.arbitrage_consistent_strike_sorted_set, quote)
                quote_slice.remove_quote_from_sorted_quote_list(quote)


    def attempt_forward_surface_filter_of_quote_slice(self, quote_slice):
        quote_slice.arbitrage_consistent_strike_sorted_set = quote_slice.compute_initial_arbitrage_consistent_set()
        self.initial_fill_arbitrage_consistent_set_forward(quote_slice)
        self.fill_arbitrage_consistent_set_with_adjusted_quotes_surface_forward(quote_slice)
        quote_slice.set_filtered_sorted_quote_list()

        if self.previous_premium_exceeds_upper_bound(quote_slice):
            raise PreviousPremiumTooHighException


    def compute_scaling_factor_expiry_lower_bound(self, quote_slice_T1, quote_slice_T2):

        forward_T1 = quote_slice_T1.forward
        discount_factor_T1 = quote_slice_T1.discount_factor
        forward_T2 = quote_slice_T2.forward
        discount_factor_T2 = quote_slice_T2.discount_factor

        return discount_factor_T2/discount_factor_T1 * forward_T2/forward_T1


    def compute_infimum_for_moneyness_filtered_slices(self, moneyness, quote_slice):
        infimum = -inf

        for index in self.filtered_slices_indices:
            quote_slice_previous_expiry = self.sorted_quote_slices[index]
            lower_bound = self.compute_scaling_factor_expiry_lower_bound(quote_slice_previous_expiry, quote_slice)* \
                          quote_slice_previous_expiry.compute_lower_bound_for_moneyness(moneyness)
            if lower_bound > infimum:
                infimum = lower_bound

        return infimum


    def bump_first_ranked_call_price(self, quote_slice, bump_size):
        first_ranked_quote = quote_slice.get_first_ranked_quote()
        new_call_premium = first_ranked_quote.call_premium + bump_size
        first_ranked_quote.adjust(new_call_premium, quote_slice.forward, quote_slice.discount_factor)


    def compute_scaled_distance_first_ranked_to_max_call_price(self, quote_slice):
        max_call_premium = quote_slice.compute_theoretical_maximum_price()
        first_ranked_quote = quote_slice.get_first_ranked_quote()
        return (max_call_premium - first_ranked_quote.call_premium) / MAXIMUM_NUMBER_OF_FAILED_ATTEMPTS


    def truncate_first_ranked_quote_forward_filtering(self, quote_slice):
        first_ranked_quote = quote_slice.get_first_ranked_quote()

        theoretical_lower_bound = quote_slice.compute_theoretical_minimum_price(first_ranked_quote.strike)
        theoretical_upper_bound = quote_slice.compute_theoretical_maximum_price()

        moneyness = first_ranked_quote.strike/quote_slice.forward
        infimum_for_moneyness = self.compute_infimum_for_moneyness_filtered_slices(moneyness, quote_slice)
        lower_bound = max(theoretical_lower_bound, infimum_for_moneyness)

        quote_slice.adjust_quote(first_ranked_quote, lower_bound, theoretical_upper_bound)


    def forward_surface_filter_for_index(self, index):
        quote_slice = self.sorted_quote_slices[index]
        original_quote_slice = deepcopy(quote_slice)

        self.truncate_first_ranked_quote_forward_filtering(quote_slice)
        scaled_distance_first_ranked_to_max_call_price = self.compute_scaled_distance_first_ranked_to_max_call_price(
            quote_slice)

        filtering_procedure_failed = False

        for number_of_failed_filtering_attempts in range(0, MAXIMUM_NUMBER_OF_FAILED_ATTEMPTS):
            quote_slice_copy = deepcopy(quote_slice)
            try:
                self.attempt_forward_surface_filter_of_quote_slice(quote_slice)
                break
            except (LowerBoundMoneynessTooHighException, PreviousPremiumTooHighException):
                quote_slice = quote_slice_copy
                next_attempt_is_final_attempt = number_of_failed_filtering_attempts == \
                                                (MAXIMUM_NUMBER_OF_FAILED_ATTEMPTS - 1)

                if next_attempt_is_final_attempt:
                    quote_slice.final_safeguard_attempt_surface()
                    filtering_procedure_failed = self.previous_premium_exceeds_upper_bound(quote_slice)
                else:
                    self.bump_first_ranked_call_price(quote_slice, scaled_distance_first_ranked_to_max_call_price)

        if filtering_procedure_failed:
            quote_slice = original_quote_slice
            quote_slice.filter_in_strike_dimension_with_safeguard()

        self.sorted_quote_slices[index] = quote_slice  # to deal with by object reference
        quote_slice.is_filtered = True


    def forward_surface_filter_for_index_with_safeguard(self, index):
        np.random.seed(PROPER_RANDOM_SEED)
        percentage_quotes_adjusted = inf
        adjustments_are_acceptable = False
        master_quote_slice = deepcopy(self.sorted_quote_slices[index])

        for number_of_attempts in range(1, MAXIMUM_NUMBER_OF_ATTEMPTS + 1):
            self.forward_surface_filter_for_index(index)
            new_percentage_quotes_adjusted = self.sorted_quote_slices[index].compute_percentage_of_quotes_adjusted()

            if new_percentage_quotes_adjusted < percentage_quotes_adjusted:
                percentage_quotes_adjusted = new_percentage_quotes_adjusted
                best_quote_slice = self.sorted_quote_slices[index]
                adjustments_are_acceptable = percentage_quotes_adjusted <= MAXIMUM_PERCENTAGE_OF_QUOTES_ADJUSTED

            if adjustments_are_acceptable:
                break
            elif number_of_attempts < MAXIMUM_NUMBER_OF_ATTEMPTS:  # loop not finished
                self.sorted_quote_slices[index] = deepcopy(master_quote_slice)
                shuffle(self.sorted_quote_slices[index].sorted_quote_list)

        self.sorted_quote_slices[index] = best_quote_slice


    def is_valid_expiry_index(self, index):
        return 0 <= index <= self.number_of_slices - 1


    def filter_surface_forward(self, use_safeguard = True):
        self.sorted_quote_slices[0].filter_in_strike_dimension_with_safeguard()
        self.filtered_slices_indices.append(0)

        filter_function = self.forward_surface_filter_for_index_with_safeguard if use_safeguard else \
            self.forward_surface_filter_for_index

        if self.is_valid_expiry_index(1):
            for index in range(1, self.number_of_slices):
                filter_function(index)
                self.filtered_slices_indices.append(index)

        self.is_filtered = True


    """ ##################### Plot functions ##################### """

    def set_plot_parameters_surface(self, maximum_moneyness):
        quote_0_expiry1 = self.sorted_quote_slices[0].compute_quote0()
        quote_0_expiry_2 = self.sorted_quote_slices[1].compute_quote0()
        max_price = max(quote_0_expiry1.call_premium, quote_0_expiry_2.call_premium)

        plt.legend(loc=0, prop={'size': 12})
        plt.xlabel("$M$")
        plt.ylabel("Call price")
        plt.xlim(-0.02, maximum_moneyness)
        plt.ylim(-0.01, max_price + 0.02)


    def plot_lower_and_upper_bounds_surface(self, quote_slice2, moneyness_values):
        lower_bounds = [max( quote_slice2.compute_lower_bound_for_moneyness(moneyness),
                             self.compute_infimum_for_moneyness_filtered_slices(moneyness, quote_slice2) )
                             for moneyness in moneyness_values]
        upper_bounds = [quote_slice2.compute_upper_bound_for_moneyness(moneyness) for moneyness in moneyness_values]

        plt.plot(moneyness_values, lower_bounds, color = 'b', label = "Lower bound $T_2$")
        plt.plot(moneyness_values, upper_bounds, color = 'r', label = "Upper bound $T_2$")


    def plot_arbitrage_consistent_set_and_bounds_surface(self, quote_slice2, moneyness_values, subplot_index, s = 40):
        a2 = quote_slice2.arbitrage_consistent_strike_sorted_set

        plt.subplot(3, 3, subplot_index)

        self.plot_lower_and_upper_bounds_surface(quote_slice2, moneyness_values)
        self.plot_first_slice_filtered()

        expiry2 = quote_slice2.expiry
        plt.scatter([quote.strike for quote in a2], [quote.call_premium for quote in a2], color = 'm',
                    label="$\mathbb{A}$" + " at $T_2$ = {:}".format(expiry2), s = s)


    def plot_first_slice_filtered(self, s = 40):
        a = self.sorted_quote_slices[0].arbitrage_consistent_strike_sorted_set
        expiry1 = self.sorted_quote_slices[0].expiry

        plt.scatter([quote.moneyness for quote in a], [quote.call_premium for quote in a], color = 'k',
                 label = "$\mathbb{A}$" + " at $T_1$ = {:}".format(expiry1), s = s)


    def plot_first_slice_filtered_and_second_unfiltered(self, moneyness_values, quote_slice2, subplot_index, s = 40):
        plt.subplot(3,3,subplot_index)
        quote_slice1 = self.sorted_quote_slices[0]

        infima = [self.compute_scaling_factor_expiry_lower_bound(quote_slice1,quote_slice2) *
                  self.compute_infimum_for_moneyness_filtered_slices(moneyness, quote_slice1) for moneyness in
                  moneyness_values]

        plt.plot(moneyness_values, infima, color = 'b', label = "Lower bound $T_1$")

        self.plot_first_slice_filtered(s)

        sorted_quote_list2 = self.sorted_quote_slices[1].sorted_quote_list
        expiry2 = self.sorted_quote_slices[1].expiry
        plt.scatter([quote.moneyness for quote in sorted_quote_list2], [quote.call_premium for quote in
            sorted_quote_list2], color = 'm', label="Original data at $T_2 = $ {:}".format(expiry2), s = s)

        self.set_plot_parameters_surface(max(moneyness_values))


    def plot_filter_in_expiry_dimension(self, maximum_moneyness, s = 40):
        """ This function plots the filtering procedure in the expiry dimension for the first two slices of a
         QuoteSurface object. """

        plt.figure()
        moneyness_values = np.linspace(0.0, maximum_moneyness, num = 1000)

        self.sorted_quote_slices[0].filter_in_strike_dimension_with_safeguard()
        self.filtered_slices_indices.append(0)


        quote_slice2 =  self.sorted_quote_slices[1]
        self.plot_first_slice_filtered_and_second_unfiltered(moneyness_values, quote_slice2, subplot_index=1, s = s)

        quote_slice2.arbitrage_consistent_strike_sorted_set = quote_slice2.compute_initial_arbitrage_consistent_set()
        a2 = quote_slice2.arbitrage_consistent_strike_sorted_set

        self.plot_arbitrage_consistent_set_and_bounds_surface(quote_slice2, moneyness_values, subplot_index = 2, s = s)
        self.set_plot_parameters_surface(max(moneyness_values))

        subplot_index = 3

        # initial fill of arbitrage consistent_set
        for quote in quote_slice2.sorted_quote_list[:]:
            self.plot_arbitrage_consistent_set_and_bounds_surface(quote_slice2, moneyness_values, subplot_index, s = s)
            plt.scatter(quote.strike, quote.call_premium, label="New quote", color="g", s = s)
            self.set_plot_parameters_surface(max(moneyness_values))
            subplot_index += 1

            if self.is_valid_quote_forward_filtering(quote, quote_slice2):
                bisect.insort_left(a2, quote)
                quote_slice2.remove_quote_from_sorted_quote_list(quote)

        # fill arbitrage consistent set with adjusted quotes
        for quote in quote_slice2.sorted_quote_list:
            self.plot_arbitrage_consistent_set_and_bounds_surface(quote_slice2, moneyness_values, subplot_index, s = s)
            plt.scatter(quote.strike, quote.call_premium, label="New quote", color="g", s = s)

            self.adjust_quote_forward_filtering(quote, quote_slice2)
            bisect.insort_left(quote_slice2.arbitrage_consistent_strike_sorted_set, quote)

            plt.scatter(quote.strike, quote.call_premium, label="Adjusted quote", color="r", s = s)
            self.set_plot_parameters_surface(max(moneyness_values))
            subplot_index += 1

        self.plot_arbitrage_consistent_set_and_bounds_surface(quote_slice2, moneyness_values, subplot_index, s = s)
        self.set_plot_parameters_surface(max(moneyness_values))

        quote_slice2.set_filtered_sorted_quote_list()
        quote_slice2.is_filtered = True
        self.is_filtered = True

        """ ##################### End of plot functions ##################### """