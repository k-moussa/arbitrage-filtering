""" This module implements the InternalQuoteProcessor class. """

import numpy as np
from typing import Optional
from ..globals import *
from .quote_structures import QuoteSurface
from .quote_transformation import transform_quote, transform_quote_surface
from .filter_factory import create_filter

COL_NAMES: final = (EXPIRY_KEY, STRIKE_KEY, MID_KEY, BID_KEY, ASK_KEY, LIQ_KEY)


class InternalQuoteProcessor(OptionQuoteProcessor):
    def __init__(self,
                 quote_surface: QuoteSurface,
                 filter_type: FilterType,
                 smoothing_param: Optional[float]):

        self._quote_surface: QuoteSurface = quote_surface

        if filter_type is not FilterType.na:
            transform_quote_surface(quote_surface=self._quote_surface, 
                                    target_price_unit=PriceUnit.normalized_call,
                                    target_strike_unit=StrikeUnit.moneyness,
                                    in_place=True)
            
            arbitrage_filter = create_filter(quote_surface=quote_surface,
                                             filter_type=filter_type,
                                             smoothing_param=smoothing_param)
            arbitrage_filter.filter()

    def get_quotes(self,
                   strike_unit: StrikeUnit,
                   price_unit: PriceUnit) -> pd.DataFrame:

        quote_df = pd.DataFrame(np.nan, index=np.arange(self._quote_surface.n_quotes()), columns=COL_NAMES)
        trans_quote_surface = transform_quote_surface(quote_surface=self._quote_surface,
                                                      target_price_unit=price_unit,
                                                      target_strike_unit=strike_unit,
                                                      in_place=False)
        
        row_index = 0
        for qs in trans_quote_surface.slices:
            for q in qs.quotes:
                quote_df[EXPIRY_KEY].iloc[row_index] = qs.expiry
                quote_df[STRIKE_KEY].iloc[row_index] = q.strike
                quote_df[MID_KEY].iloc[row_index] = q(Side.mid)
                quote_df[BID_KEY].iloc[row_index] = q.bid
                quote_df[ASK_KEY].iloc[row_index] = q.ask
                quote_df[LIQ_KEY].iloc[row_index] = q.liq_proxy

                row_index += 1

        return quote_df
