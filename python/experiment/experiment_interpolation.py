

import matplotlib.pyplot as plt
import numpy as np
import numcomp as nc


def main():
    x = np.arange(start=1, stop=5)
    x_eval = np.linspace(start=0, stop=6, num=100)
    true_func = np.sin

    plot_interpolation(x=x,
                       x_eval=x_eval,
                       true_func=true_func,
                       inter_type=nc.InterpolationType.linear,
                       extra_type=nc.ExtrapolationType.flat)


def plot_interpolation(x: np.ndarray,
                       x_eval: np.ndarray,
                       true_func,
                       inter_type: nc.InterpolationType,
                       extra_type: nc.ExtrapolationType):

    y = true_func(x)
    interpolator = nc.create_interpolator(x=x, y=y, inter_type=inter_type, extra_type=extra_type)

    true_y = true_func(x_eval)
    plt.plot(x_eval, true_y, label='true', color='red')

    interp_y = interpolator(x_eval)
    plt.plot(x_eval, interp_y, label='interpolation (' + interpolator.inter_type.name + ')', color='blue', ls='--')

    plt.scatter(x, y, marker='o', label='data', color='black')
    plt.legend()


if __name__ == "__main__":
    main()
    plt.show()
