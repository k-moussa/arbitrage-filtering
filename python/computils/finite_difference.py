""" This module contains functionality for the numerical computation of derivatives using finite difference
    based on the discussion in Numerical Recipes. """

import numpy as np
from typing import Callable, Final
from .globals import CUBE_ROOT_MACHINE_EPS, FOURTH_ROOT_MACHINE_EPS, FloatOrArray
from .type_utils import size as size_func

_LOWER_BOUND_CHARACTERISTIC_SCALE: Final = 0.001


def compute_derivative(func: Callable[[float], float],
                       x: FloatOrArray,
                       order: int,
                       args: tuple = (),
                       step_size: float = None) -> FloatOrArray:
    """ Computes the first- or second-order derivative using finite differences for a given function at the point x.

    Remarks: x is assumed to correspond to the first parameter of func.

    :param func: a function f: R -> R, with x corresponding to its first parameter.
    :param x: the point(s) of interest.
    :param order: 1 or 2, the order of which to compute the derivative.
    :param args: additional arguments to the function in the correct order.
    :param step_size: a scalar > 0.
    :return: the fd estimate(s) of the first-order derivative.
    """

    if order != 1 and order != 2:
        raise RuntimeError("order must be 1 or 2.")

    scalar_input = size_func(x) == 1
    if scalar_input:
        x = np.array([x])

    fd_derivatives = np.full(fill_value=np.nan, shape=x.shape)
    x_arg = np.full(fill_value=np.nan, shape=(1,))
    for i in range(x.size):
        x_arg[0] = x[i]
        if order == 1:
            fd_derivatives[i] = compute_gradient(func=func, x=x_arg, args=args, step_size=step_size)[0]
        else:  # order == 2:
            fd_derivatives[i] = compute_hessian(func=func, x=x_arg, args=args, step_size=step_size)[0, 0]

    if scalar_input:
        return fd_derivatives[0]
    else:
        return fd_derivatives


def compute_gradient(func: Callable[..., float],
                     x: np.ndarray,
                     args: tuple = (),
                     step_size: float = None) -> np.ndarray:
    """ Computes the gradient using finite differences for a given function at the point x.

    Remarks: x is assumed to correspond to the first parameter of func.

    :param func: a function f: R^n -> R, with x corresponding to its first parameter.
    :param x: an (n,) np array corresponding to the point of interest.
    :param args: additional arguments to the function in the correct order.
    :param step_size: a scalar > 0.
    :return: an (n, 1) array containing the numerical approximation of the gradient.
    """

    jacobian = compute_jacobian(func=func, x=x, args=args, step_size=step_size)
    gradient = jacobian.T
    return gradient


def compute_jacobian(func: Callable[[np.ndarray], np.ndarray],
                     x: np.ndarray,
                     args: tuple = (),
                     step_size: float = None) -> np.ndarray:
    """ Computes the Jacobian using finite differences for a given function at the point x.

    :param func: a function f: R^n -> R^m (i.e. returns an (m,) np array of function values), with x corresponding to
        its first parameter.
    :param x: an (n,) np array corresponding to the point of interest.
    :param args: additional arguments to the function in the correct order.
    :param step_size: a scalar > 0.
    :return: an (m, n) array containing the numerical approximation of the Jacobian.
    """

    func = _get_func_given_args(func, args)

    function_value = func(x)
    if isinstance(function_value, np.ndarray):
        m = func(x).size
    else:
        m = 1

    n = x.size
    jacobian = np.zeros((m, n))
    step_sizes = get_step_sizes(x, derivative_order=1, step_size=step_size)

    for i in range(n):
        selection_vector = _get_selection_vector(n, index=i)

        if m == 1:
            jacobian[0, i] = _compute_1st_derivative_fd(func, x, step_sizes[i], selection_vector)
        else:
            jacobian[:, i] = _compute_1st_derivative_fd(func, x, step_sizes[i], selection_vector)

    return jacobian


def compute_hessian(func: Callable[[np.ndarray], float],
                    x: np.ndarray,
                    args: tuple = (),
                    step_size: float = None) -> np.ndarray:
    """ Computes the Hessian matrix using finite differences for a given function at the point x.

    :param func: a function f: R^n -> R, with x corresponding to its first parameter..
    :param x: an (n,) np array corresponding to the point of interest.
    :param args: additional arguments to the function in the correct order.
    :param step_size: a scalar > 0.
    :return: an (n, n) array containing the numerical approximation of the hessian.
    """

    func = _get_func_given_args(func, args)

    n = x.size
    hessian = np.zeros((n, n))
    step_sizes = get_step_sizes(x, derivative_order=2, step_size=step_size)

    for i in range(n):
        for j in range(i, n):
            step_size = step_sizes[i, j]
            selection_vector_i = _get_selection_vector(n, index=i)
            selection_vector_j = _get_selection_vector(n, index=j)
            hessian[i, j] = _compute_2nd_derivative_fd(func, x, step_size, selection_vector_i, selection_vector_j)

    diagonal = np.diag(hessian).copy()
    hessian += hessian.T
    np.fill_diagonal(hessian, diagonal)

    return hessian


def _get_func_given_args(func: Callable[..., FloatOrArray], args: tuple = ()) -> Callable[[np.ndarray], FloatOrArray]:
    return lambda x: func(x, *args)


def get_step_sizes(x: np.ndarray,
                   derivative_order: int,
                   step_size: float = None) -> np.ndarray:
    """ Returns an (x.size, 1) array for derivative_order 1, and an (x.size, x.size) array for derivative_order 2 """

    if step_size is None:
        optimal_relative_step_size = _get_optimal_relative_step_size(derivative_order)
        abs_curvature_scale_estimates = _get_abs_curvature_scale_estimates(x, derivative_order)
        optimal_step_sizes = optimal_relative_step_size * abs_curvature_scale_estimates

        # trick from Numerical Recipes to ensure that x + h and x differ by an exactly-representable number
        x_2dim = x.copy()
        x_2dim.shape = (x_2dim.size, 1)
        temp = optimal_step_sizes + x_2dim
        optimal_step_sizes = temp - x_2dim

        return optimal_step_sizes

    elif step_size <= 0.0:
        raise RuntimeError("step_size {:.2f} <= 0 not allowed..".format(step_size))
    else:
        if derivative_order == 1:
            shape = (x.size, 1)
        elif derivative_order == 2:
            shape = (x.size, x.size)
        else:
            raise RuntimeError("derivative_order {:} not implemented.".format(derivative_order))

        step_sizes = np.full(shape=shape, fill_value=step_size)
        return step_sizes


def _get_abs_curvature_scale_estimates(x: np.ndarray,
                                       derivative_order: int) -> np.ndarray:
    """ Returns an (x.size, 1) array for derivative_order 1, and an (x.size, x.size) array for derivative_order 2 """

    if derivative_order == 1:
        abs_curvature_scale_estimates = np.clip(np.abs(x), a_min=_LOWER_BOUND_CHARACTERISTIC_SCALE, a_max=np.inf)
        abs_curvature_scale_estimates.shape = (x.size, 1)
        return abs_curvature_scale_estimates
    elif derivative_order == 2:
        abs_x = np.abs(x)
        abs_x.shape = (abs_x.size, 1)
        abs_curvature_scale_estimates = (abs_x + abs_x.T) / 2.0  # use the average argument values as estimates
        return np.clip(abs_curvature_scale_estimates, a_min=_LOWER_BOUND_CHARACTERISTIC_SCALE, a_max=np.inf)
    else:
        raise RuntimeError("derivative_order {:} not implemented.".format(derivative_order))


def _get_optimal_relative_step_size(derivative_order: int) -> float:
    if derivative_order == 1:
        return CUBE_ROOT_MACHINE_EPS
    elif derivative_order == 2:
        return FOURTH_ROOT_MACHINE_EPS
    else:
        raise RuntimeError("derivative_order {:} not implemented.".format(derivative_order))


def _get_selection_vector(size: int,
                          index: int) -> np.ndarray:
    selection_vector = np.zeros((size,))
    selection_vector[index] = 1.0

    return selection_vector


def _compute_1st_derivative_fd(func: Callable[[np.ndarray], FloatOrArray],
                               x: np.ndarray,
                               step_size: float,
                               selection_vector: np.ndarray) -> FloatOrArray:
    """ Computes either a single 1st-order derivative, or an entire column of the Jacobian matrix. """

    step_size_selection_vector = step_size * selection_vector
    forward_value = func(x + step_size_selection_vector)
    backward_value = func(x - step_size_selection_vector)

    fd_approximation = (forward_value - backward_value) / (2.0 * step_size)
    return fd_approximation


def _compute_2nd_derivative_fd(func: Callable[[np.ndarray], float],
                               x: np.ndarray,
                               step_size: float,
                               selection_vector_i: np.ndarray,
                               selection_vector_j: np.ndarray) -> float:
    step_size_selection_vector_i = step_size * selection_vector_i
    step_size_selection_vector_j = step_size * selection_vector_j

    func_value_plus_i_plus_j = func(x + step_size_selection_vector_i + step_size_selection_vector_j)
    func_value_plus_i_minus_j = func(x + step_size_selection_vector_i - step_size_selection_vector_j)
    func_value_minus_i_plus_j = func(x - step_size_selection_vector_i + step_size_selection_vector_j)
    func_value_minus_i_minus_j = func(x - step_size_selection_vector_i - step_size_selection_vector_j)

    fd_approximation = (func_value_plus_i_plus_j - func_value_plus_i_minus_j - func_value_minus_i_plus_j +
                        func_value_minus_i_minus_j) / (4.0 * step_size ** 2)
    return fd_approximation
