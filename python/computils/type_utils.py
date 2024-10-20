""" Implements helping functions for the introduced types. """

import numpy as np
from .globals import ScalarOrArray


def size(x: ScalarOrArray) -> int:
    if isinstance(x, np.ndarray):
        return x.size
    else:
        return 1
