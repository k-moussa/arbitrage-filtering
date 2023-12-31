""" This module implements the InternalQuoteProcessor class. """

import numpy as np
from copy import deepcopy
from ..globals import *
from .arbitrage_filter import create_filter, ArbitrageFilter
from .quote_structures import QuoteSurface
from .quote_transformation import transform_strike, transform_price, transform_quote

COL_NAMES: final = (EXPIRY_KEY, STRIKE_KEY, MID_KEY, BID_KEY, ASK_KEY, LIQ_KEY)


class BoundType(Enum):
    lower = 1
    upper = 2


class InternalQuoteProcessor(OptionQuoteProcessor):
    def __init__(self,
                 quote_surface: QuoteSurface,
                 forward_curve: ForwardCurve,
                 rate_curve: RateCurve):

        self._quote_surface: QuoteSurface = quote_surface
        self._forward_curve: ForwardCurve = forward_curve
        self._rate_curve: RateCurve = rate_curve
        self._arbitrage_filter: Optional[ArbitrageFilter] = None

    def transform_strike(self,
                         expiry: float,
                         strike: ScalarOrArray,
                         input_strike_unit: StrikeUnit,
                         output_strike_unit: StrikeUnit) -> ScalarOrArray:

        forward = self._forward_curve.get_forward(expiry)
        return transform_strike(strike=strike, input_strike_unit=input_strike_unit,
                                output_strike_unit=output_strike_unit, forward=forward)

    def transform_price(self,
                        strike: ScalarOrArray,
                        strike_unit: StrikeUnit,
                        price: ScalarOrArray,
                        input_price_unit: PriceUnit,
                        output_price_unit: PriceUnit,
                        expiry: float) -> ScalarOrArray:

        forward = self._forward_curve.get_forward(expiry)
        discount_factor = self._rate_curve.get_discount_factor(expiry)
        return transform_price(strike=strike, strike_unit=strike_unit, price=price, input_price_unit=input_price_unit,
                               output_price_unit=output_price_unit, expiry=expiry, discount_factor=discount_factor,
                               forward=forward)

    def filter(self,
               filter_type: FilterType,
               smoothing_param: Optional[float] = DEFAULT_SMOOTHING_PARAM,
               param_grid: Tuple[float] = DEFAULT_SMOOTHING_PARAM_GRID):

        self.transform_quote_surface(quote_surface=self._quote_surface,
                                     output_price_unit=PriceUnit.normalized_call,
                                     output_strike_unit=StrikeUnit.moneyness,
                                     in_place=True)

        self._arbitrage_filter = create_filter(quote_surface=self._quote_surface,
                                               filter_type=filter_type,
                                               smoothing_param=smoothing_param,
                                               smoothing_param_grid=param_grid)

        self._arbitrage_filter.filter()

    def compute_lower_bound(self,
                            expiry: float,
                            strike: ScalarOrArray,
                            strike_unit: StrikeUnit,
                            price_unit: PriceUnit) -> ScalarOrArray:

        return self._compute_bound(expiry=expiry, strike=strike, strike_unit=strike_unit, price_unit=price_unit, 
                                   bound_type=BoundType.lower)

    def compute_upper_bound(self,
                            expiry: float,
                            strike: ScalarOrArray,
                            strike_unit: StrikeUnit,
                            price_unit: PriceUnit) -> ScalarOrArray:

        return self._compute_bound(expiry=expiry, strike=strike, strike_unit=strike_unit, price_unit=price_unit, 
                                   bound_type=BoundType.upper)

    def _compute_bound(self,
                       expiry: float,
                       strike: ScalarOrArray,
                       strike_unit: StrikeUnit,
                       price_unit: PriceUnit,
                       bound_type: BoundType) -> ScalarOrArray:

        if not self._is_filtered():
            raise RuntimeError("bounds can only be computed if the quotes have been filtered."
                               "Call the 'filter' method before computing the bounds.")
        elif expiry not in self._quote_surface.expiries():
            # todo:  make possible for other expiries too.
            raise RuntimeError(f"expiry {expiry} not in quote expiries {self._quote_surface.expiries()}", )

        # map strike to units of quote surface
        transformed_strike = self.transform_strike(expiry=expiry, strike=strike, input_strike_unit=strike_unit,
                                                   output_strike_unit=self._quote_surface.strike_unit)
        normalized_call_bound = self._compute_normalized_call_bound(expiry=expiry,
                                                                    transformed_strike=transformed_strike,
                                                                    bound_type=bound_type)

        price_bound = self.transform_price(strike=strike, strike_unit=strike_unit, price=normalized_call_bound,
                                           input_price_unit=PriceUnit.normalized_call, output_price_unit=price_unit,
                                           expiry=expiry)
        return price_bound

    def _is_filtered(self) -> bool:
        return self._arbitrage_filter is not None

    def _compute_normalized_call_bound(self,
                                       expiry: float,
                                       transformed_strike: ScalarOrArray,
                                       bound_type: BoundType) -> ScalarOrArray:
        """ Computes the normalized call bound(s) of interest.

        :param expiry:
        :param transformed_strike: strikes in units of quote surface.
        :param bound_type:
        :return:
        """

        bound_func = self._arbitrage_filter.compute_lower_bound if bound_type is BoundType.lower else \
            self._arbitrage_filter.compute_upper_bound

        if not isinstance(transformed_strike, np.ndarray):  # scalar
            return bound_func(expiry=expiry, trans_strike=transformed_strike)
        else:
            bounds = np.full(shape=transformed_strike.shape, fill_value=np.nan)
            for i in range(transformed_strike.size):
                bounds[i] = bound_func(expiry=expiry, trans_strike=transformed_strike[i])

            return bounds

    def get_quotes(self,
                   strike_unit: StrikeUnit,
                   price_unit: PriceUnit) -> pd.DataFrame:

        quote_df = pd.DataFrame(np.nan, index=np.arange(self._quote_surface.n_quotes()), columns=COL_NAMES)
        trans_quote_surface = self.transform_quote_surface(quote_surface=self._quote_surface,
                                                           output_price_unit=price_unit,
                                                           output_strike_unit=strike_unit,
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

    def transform_quote_surface(self,
                                quote_surface: QuoteSurface,
                                output_price_unit: PriceUnit,
                                output_strike_unit: StrikeUnit,
                                in_place: bool) -> QuoteSurface:

        if in_place:
            trans_quote_surface = quote_surface
        else:
            trans_quote_surface = deepcopy(quote_surface)

        for qs in trans_quote_surface.slices:
            expiry = qs.expiry
            forward = self._forward_curve.get_forward(expiry)
            discount_factor = self._rate_curve.get_discount_factor(expiry)
            for q in qs.quotes:
                transform_quote(q=q,
                                input_price_unit=quote_surface.price_unit,
                                output_price_unit=output_price_unit,
                                input_strike_unit=quote_surface.strike_unit,
                                output_strike_unit=output_strike_unit,
                                expiry=expiry,
                                discount_factor=discount_factor,
                                forward=forward,
                                in_place=True)

        trans_quote_surface.price_unit = output_price_unit
        trans_quote_surface.strike_unit = output_strike_unit
        return trans_quote_surface
