""" This module implements the InternalQuoteProcessor class. """

import numpy as np
from typing import Optional
from ..globals import *
from .quote_structures import QuoteSurface
from .quote_transformation import transform_quote
from .filter_factory import create_filter

COL_NAMES: final = (EXPIRY_KEY, STRIKE_KEY, MID_KEY, BID_KEY, ASK_KEY, LIQ_KEY)


class InternalQuoteProcessor(OptionQuoteProcessor):
    def __init__(self,
                 quote_surface: QuoteSurface,
                 filter_type: FilterType,
                 smoothing_param: Optional[float]):

        self._quote_surface: QuoteSurface = quote_surface

        if filter_type is not FilterType.na:
            arbitrage_filter = create_filter(quote_surface=quote_surface,
                                             filter_type=filter_type,
                                             smoothing_param=smoothing_param)
            arbitrage_filter.filter()

    def get_quotes(self,
                   strike_unit: StrikeUnit,
                   price_unit: PriceUnit) -> pd.DataFrame:

        current_price_unit = self._quote_surface.price_unit
        current_strike_unit = self._quote_surface.strike_unit
        quote_df = pd.DataFrame(np.nan, index=np.arange(self._quote_surface.n_quotes()), columns=COL_NAMES)
        row_index = 0
        for qs in self._quote_surface.slices:
            for q in qs.quotes:
                quote_df[EXPIRY_KEY].iloc[row_index] = qs.expiry
                
                q_trans = transform_quote(q=q,
                                          price_unit=current_price_unit,
                                          target_price_unit=price_unit,
                                          strike_unit=current_strike_unit,
                                          target_strike_unit=strike_unit,
                                          expiry=qs.expiry,
                                          discount_factor=qs.discount_factor,
                                          forward=qs.forward,
                                          in_place=False)
                quote_df[STRIKE_KEY].iloc[row_index] = q_trans.strike
                quote_df[MID_KEY].iloc[row_index] = q_trans(Side.mid)
                quote_df[BID_KEY].iloc[row_index] = q_trans.bid
                quote_df[ASK_KEY].iloc[row_index] = q_trans.ask
                quote_df[LIQ_KEY].iloc[row_index] = q_trans.liq_proxy

                row_index += 1

        return quote_df
