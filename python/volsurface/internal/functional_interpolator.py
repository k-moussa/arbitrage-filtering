""" This module implements the FunctionalInterpolator class. """

import numpy as np
from enum import Enum
from bisect import bisect_left
from typing import List, Callable, Tuple, Union
import numcomp as nc


class FuncInterType(Enum):
    linear = 0


def compute_weights(x: float,
                    x_left: float,
                    x_right: float,
                    f_inter_type: FuncInterType) -> Tuple[float, float]:

    if f_inter_type is FuncInterType.linear:
        w_left = (x - x_left) / (x_right - x_left)
        w_right = 1.0 - w_left
        return w_left, w_right
    else:
        raise RuntimeError(f"Unhandled FuncInterType {FuncInterType.name}.")


class FunctionalInterpolator:
    def __init__(self,
                 independent_variables: np.ndarray,
                 funcs: List[Callable[[nc.ScalarOrArray], nc.ScalarOrArray]],
                 f_inter_type: FuncInterType):

        self.independent_variables: np.ndarray = independent_variables
        self.funcs: List[Callable[[nc.ScalarOrArray], nc.ScalarOrArray]] = funcs
        self.f_inter_type: FuncInterType = f_inter_type

    def __call__(self,
                 x: nc.Scalar,
                 z: nc.ScalarOrArray) -> nc.ScalarOrArray:

        func = self.get_func(x)
        return func(z)

    def get_func(self, x: nc.Scalar) -> Callable[[nc.ScalarOrArray], nc.ScalarOrArray]:
        indices = self._get_indices(x)
        if isinstance(indices, int):
            return self.funcs[indices]

        x_left = self.independent_variables[indices[0]]
        x_right = self.independent_variables[indices[1]]
        w_left, w_right = compute_weights(x=x, x_left=x_left, x_right=x_right, f_inter_type=self.f_inter_type)

        func = lambda z: w_left * self.funcs[indices[0]](z) + w_right * self.funcs[indices[1]](z)
        return func

    def _get_indices(self, x: nc.Scalar) -> Union[int, Tuple[int, int]]:
        i = bisect_left(self.independent_variables, x)
        if i == self.independent_variables.size:  # exceeds rhs
            return -1
        elif x < self.independent_variables[0]:  # exceeds lhs
            return 0
        elif x == self.independent_variables[i]:
            return i
        else:  # value bracketed by x[i-1] and x[i]
            return i-1, i
