""" This module serves as the interface of the numcomp package.

    References:
        FC80: Frederick N. Fritsch and Ralph E. Carlson. Monotone piecewise cubic interpolation. SIAM Journal on
            Numerical Analysis, 17(2):238–246, 1980. doi:10.1137/0717021.
        FB84: Frederick N. Fritsch and Judy Butland. A method for constructing local monotone piecewise cubic
            interpolants. SIAM Journal on Scientific and Statistical Computing, 5(2):300–304, 1984. doi:10.1137/0905021.
"""

from .globals import *
from .factory import create_interpolator
