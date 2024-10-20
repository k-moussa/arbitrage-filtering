""" This module collects all exposed types."""

import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
from typing import final, Union

MACHINE_EPS: final = float(2 ** (-53))  # max relative error corresponding to 1/2 ULP
SQUARE_ROOT_MACHINE_EPS: final = np.sqrt(MACHINE_EPS)
CUBE_ROOT_MACHINE_EPS: final = np.cbrt(MACHINE_EPS)
FOURTH_ROOT_MACHINE_EPS: final = np.power(MACHINE_EPS, 1/4)

Integer: final = Union[int, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64]
Float: final = Union[float, np.float16, np.float32, np.float64, np.float128]
Complex: final = Union[complex, np.complex64, np.complex128, np.complex256]
Scalar: final = Union[Integer, Float, Complex]

IntOrArray: final = Union[Integer, np.ndarray]
FloatOrArray: final = Union[Float, np.ndarray]
ComplexOrArray: final = Union[Complex, np.ndarray]
ScalarOrArray: final = Union[Scalar, np.ndarray]


class InterpolationType(Enum):
    linear = 0
    ncs = 1  # natural cubic spline
    ccs = 2  # clamped cubic spline
    pmc = 3  # piecewise monotone cubic [FC80]
    pchip = 4  # [FB84]


class ExtrapolationType(Enum):
    nan = 0
    flat = 1


class Interpolator(ABC):
    def __init__(self,
                 inter_type: InterpolationType,
                 extra_type: ExtrapolationType):

        self.inter_type: InterpolationType = inter_type
        self.extra_type: ExtrapolationType = extra_type

    @abstractmethod
    def __call__(self, x: ScalarOrArray) -> ScalarOrArray:
        """

        :param x:
        :return:
        """
