""" This module implements various interpolation methods. """

from typing import Optional, Callable
from .globals import *


def size(x: ScalarOrArray) -> int:
    if isinstance(x, np.ndarray):
        return x.size
    else:
        return 1


class InternalInterpolator(Interpolator, ABC):
    def __init__(self,
                 x: np.ndarray,
                 y: np.ndarray,
                 inter_type: InterpolationType,
                 extra_type: ExtrapolationType):
        """

        :param x: independent variables; data must be sorted in ascending order.
        :param y: dependent variables corresponding to x.
        :param inter_type:
        :param extra_type:
        """

        super().__init__(inter_type=inter_type, extra_type=extra_type)

        self._x: np.ndarray = x  # independent variables
        self._y: np.ndarray = y  # dependent variables
        self._interpolant: Callable[[ScalarOrArray], ScalarOrArray] = self._get_interpolant(x=x, y=y,
                                                                                            inter_type=inter_type)

    def __call__(self, x: ScalarOrArray) -> ScalarOrArray:
        """

        :param x:
        :return:
        """

        y = self._interpolant(x)
        extra_masks = self._get_extrapolation_masks(x)
        no_extrapolation = np.sum(extra_masks) == 0
        if no_extrapolation:
            return y
        else:
            y[extra_masks] = self._extrapolate(x[extra_masks])

        return y

    def _get_extrapolation_masks(self, x: ScalarOrArray) -> IntOrArray:
        """ Returns masks for points in extrapolation region. """

        return self._exceeds_lhs(x) | self._exceeds_rhs(x)

    def _exceeds_lhs(self, x: ScalarOrArray) -> IntOrArray:
        return x < self._x[0]

    def _exceeds_rhs(self, x: ScalarOrArray) -> IntOrArray:
        return x > self._x[-1]

    def _extrapolate(self, x_extra: ScalarOrArray) -> ScalarOrArray:
        y_extra = np.full(shape=(size(x_extra),), fill_value=np.nan)
        if self.extra_type is ExtrapolationType.nan:
            return y_extra

        lhs_masks = self._exceeds_lhs(x_extra)
        rhs_masks = self._exceeds_rhs(x_extra)
        if self.extra_type is ExtrapolationType.flat:
            y_extra[lhs_masks] = self._y[0]
            y_extra[rhs_masks] = self._y[-1]

        return y_extra

    @staticmethod
    def _get_interpolant(x: np.ndarray,
                         y: np.ndarray,
                         inter_type: InterpolationType) -> Callable[[ScalarOrArray], ScalarOrArray]:

        if inter_type is InterpolationType.linear:
            interpolant = lambda z: np.interp(x=z, xp=x, fp=y)
            return interpolant
        else:
            raise RuntimeError(f"Unhandled inter_type {inter_type.name}.")
