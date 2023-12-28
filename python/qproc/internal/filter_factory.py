""" This module serves to create instances of the ArbitrageFilter class. """

from typing import Optional, Tuple
from ..globals import FilterType
from .quote_structures import QuoteSurface
from .arbitrage_filter.globals import ArbitrageFilter
from .arbitrage_filter.arbitrage_filter import StrikeFilter, ForwardExpiryFilter, DiscardFilter


def create_filter(quote_surface: QuoteSurface,
                  filter_type: FilterType,
                  smoothing_param: Optional[float],
                  smoothing_param_grid: Tuple[float]) -> ArbitrageFilter:

    if filter_type is FilterType.strike:
        return StrikeFilter(quote_surface=quote_surface, smoothing_param=smoothing_param,
                            smoothing_param_grid=smoothing_param_grid)
    elif filter_type is FilterType.expiry_forward:
        return ForwardExpiryFilter(quote_surface=quote_surface, smoothing_param=smoothing_param,
                                   smoothing_param_grid=smoothing_param_grid)
    elif filter_type is FilterType.discard:
        return DiscardFilter(quote_surface=quote_surface, smoothing_param=smoothing_param,
                             smoothing_param_grid=smoothing_param_grid)
    else:
        raise RuntimeError(f"filter_type {filter_type.name} not implemented.")
