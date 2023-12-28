""" This module serves to create instances of the ArbitrageFilter class. """

from typing import Optional
from ..globals import FilterType
from .quote_structures import QuoteSurface
from .arbitrage_filter.globals import ArbitrageFilter
from .arbitrage_filter.arbitrage_filter import StrikeFilter, DiscardFilter


def create_filter(quote_surface: QuoteSurface,
                  filter_type: FilterType,
                  smoothing_param: Optional[float]) -> ArbitrageFilter:

    if filter_type is FilterType.strike:
        return StrikeFilter(quote_surface=quote_surface, smoothing_param=smoothing_param)
    elif filter_type is FilterType.discard:
        return DiscardFilter(quote_surface=quote_surface, smoothing_param=smoothing_param)
    else:
        raise RuntimeError(f"filter_type {filter_type.name} not implemented.")
