""" This module allows for creating instances of the VolSurface class. """

from typing import Optional
from numcomp import InterpolationType
from qproc import OptionQuoteProcessor, FilterType
from .globals import VolSurface
from .internal.vol_surface import InternalVolSurface


def create(smile_inter_type: InterpolationType,
           oqp: OptionQuoteProcessor,
           filter_type: Optional[FilterType] = FilterType.strike,
           filter_smoothness_param: float = 0.01) -> VolSurface:

    return InternalVolSurface(smile_inter_type=smile_inter_type,
                              oqp=oqp,
                              filter_type=filter_type,
                              filter_smoothness_param=filter_smoothness_param)
