""" This module provides visual tests of the implementation of several curves. """

import numpy as np
import matplotlib.pyplot as plt
import qproc
from data import DataSetName, get_option_data, OptionDataSet


def main():
    option_data = get_option_data(DataSetName.dax_13_jun_2000)
    plot_rates(option_data)
    plot_forwards(option_data)


def plot_rates(option_data: OptionDataSet):
    plt.figure()
    expiries = option_data.unique_expiries()
    zero_rates = option_data.rates
    rate_curve = qproc.create_rate_curve(times=expiries, zero_rates=zero_rates)

    times_for_plot = np.linspace(start=0.0, stop=expiries[-1] * 1.1, num=500)
    rates_for_plot = rate_curve.get_zero_rate(times_for_plot)
    plt.plot(times_for_plot, rates_for_plot, label='rates', color='cornflowerblue')

    plt.scatter(expiries, zero_rates, label='data', marker='o', color='black')
    plt.xlabel('$T$')
    plt.ylabel('$r(T)$')
    plt.legend()
    plt.title('Zero rates (' + option_data.name.name + ')')

    plt.figure()
    discount_factors_for_plot = rate_curve.get_discount_factor(times_for_plot)
    plt.plot(times_for_plot, discount_factors_for_plot, label='discount factors', color='cornflowerblue')
    plt.xlabel('$T$')
    plt.ylabel('$B(T)$')
    plt.legend()
    plt.title('Discount factors (' + option_data.name.name + ')')


def plot_forwards(option_data: OptionDataSet):
    plt.figure()
    expiries = option_data.unique_expiries()
    forwards = option_data.forwards
    forward_curve = qproc.create_forward_curve(spot=option_data.spot, times=expiries, forwards=forwards)

    times_for_plot = np.linspace(start=0.0, stop=expiries[-1] * 1.1, num=500)
    forwards_for_plot = forward_curve.get_forward(times_for_plot)
    plt.plot(times_for_plot, forwards_for_plot, label='forwards', color='cornflowerblue')

    plt.scatter(expiries, forwards, label='data', marker='o', color='black')
    plt.scatter(np.zeros(1), np.array([forward_curve.spot()]), label='spot', marker='o', color='red')
    plt.xlabel('$T$')
    plt.ylabel('$F(T)$')
    plt.legend()
    plt.title('Forwards (' + option_data.name.name + ')')


if __name__ == "__main__":
    main()
    plt.show()
