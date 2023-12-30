

import matplotlib.pyplot as plt
import numpy as np
# from typing import List, Union
import numcomp as nc


def main():
    extra_type = nc.ExtrapolationType.flat
    inter_types = [nc.InterpolationType.pmc, nc.InterpolationType.pchip]

    for inter_type in [t for t in nc.InterpolationType]:
        # plot_interpolation(inter_type=inter_type, extra_type=extra_type)

        plot_monotone_data(inter_type=inter_type, extra_type=extra_type)


def plot_interpolation(inter_type: nc.InterpolationType,
                       extra_type: nc.ExtrapolationType):
    plt.figure()

    x = np.arange(start=1, stop=5)
    x_eval = np.linspace(start=0, stop=6, num=100)
    true_func = np.sin

    y = true_func(x)
    interpolator = nc.create_interpolator(x=x, y=y, inter_type=inter_type, extra_type=extra_type)

    true_y = true_func(x_eval)
    plt.plot(x_eval, true_y, label='true', color='red')

    interp_y = interpolator(x_eval)
    plt.plot(x_eval, interp_y, label='interpolation (' + interpolator.inter_type.name + ')', color='blue', ls='--')

    plt.scatter(x, y, marker='o', label='data', color='black')
    plt.legend()


def plot_monotone_data(inter_type: nc.InterpolationType,
                       extra_type: nc.ExtrapolationType):
    plt.figure()

    x = np.array([0, 3, 8, 10, 11])
    y = np.array([0, 3, 3, 7, 0])
    x_eval = np.linspace(start=-1, stop=12, num=500)

    interpolator = nc.create_interpolator(x=x, y=y, inter_type=inter_type, extra_type=extra_type)
    interp_y = interpolator(x_eval)
    plt.plot(x_eval, interp_y, label='interpolation (' + interpolator.inter_type.name + ')', color='cornflowerblue')

    plt.scatter(x, y, marker='o', label='data', color='black')
    plt.legend()


if __name__ == "__main__":
    main()
    plt.show()
