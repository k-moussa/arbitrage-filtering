""" This module implements the FunctionalInterpolator class. """

import numpy as np
from enum import Enum
from bisect import bisect_left
from typing import List, Callable, Tuple, Union
import numcomp as nc


class FuncInterType(Enum):
    linear = 0


def compute_weights(z: float,
                    z_left: float,
                    z_right: float,
                    f_inter_type: FuncInterType) -> Tuple[float, float]:

    if f_inter_type is FuncInterType.linear:
        w_left = (z - z_left) / (z_right - z_left)
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
                 x: nc.ScalarOrArray,
                 y: nc.Scalar) -> nc.ScalarOrArray:

        func = self.get_func(y)
        return func(x)

    def get_func(self, y: nc.Scalar) -> Callable[[nc.ScalarOrArray], nc.ScalarOrArray]:
        indices = self._get_indices(y)
        if isinstance(indices, int):
            return self.funcs[indices]

        y_left = self.independent_variables[indices[0]]
        y_right = self.independent_variables[indices[1]]
        w_left, w_right = compute_weights(z=y, z_left=y_left, z_right=y_right, f_inter_type=self.f_inter_type)

        func = lambda z: w_left * self.funcs[indices[0]](z) + w_right * self.funcs[indices[1]](z)
        return func

    def _get_indices(self, y: nc.Scalar) -> Union[int, Tuple[int, int]]:
        i = bisect_left(self.independent_variables, y)
        if i == self.independent_variables.size:  # exceeds rhs
            return -1
        elif y < self.independent_variables[0]:  # exceeds lhs
            return 0
        elif y == self.independent_variables[i]:
            return i
        else:  # value bracketed by x[i-1] and x[i]
            return i-1, i
