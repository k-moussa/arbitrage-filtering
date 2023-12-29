""" This module implements the InternalQuoteProcessor class. """

from copy import copy, deepcopy
from ..globals import *
from .arbitrage_filter import create_filter, ArbitrageFilter
from .quote_structures import Quote, QuoteSurface
from .volatility_functions import implied_vol_for_discounted_option, discounted_black
from .zero_strike_computation import compute_zero_strike_call_value

COL_NAMES: final = (EXPIRY_KEY, STRIKE_KEY, MID_KEY, BID_KEY, ASK_KEY, LIQ_KEY)


class BoundType(Enum):
    lower = 1
    upper = 2


class InternalQuoteProcessor(OptionQuoteProcessor):
    def __init__(self, quote_surface: QuoteSurface):
        self._quote_surface: QuoteSurface = quote_surface
        self._arbitrage_filter: Optional[ArbitrageFilter] = None

    @staticmethod
    def transform_strike(strike: ScalarOrArray,
                         strike_unit: StrikeUnit,
                         target_strike_unit: StrikeUnit,
                         forward: float) -> ScalarOrArray:

        if strike_unit is target_strike_unit:
            return strike

        strike = deepcopy(strike)   # do not overwrite input

        # map to actual strike
        if strike_unit is not StrikeUnit.strike:  # map to strike
            if strike_unit is StrikeUnit.moneyness:
                strike *= forward
            elif strike_unit is StrikeUnit.log_moneyness:
                strike = np.exp(strike) * forward
            else:
                raise RuntimeError(f"Unhandled strike_unit {strike_unit.name}")

        if target_strike_unit is StrikeUnit.strike:
            return strike
        elif target_strike_unit is StrikeUnit.moneyness:
            return strike / forward
        elif target_strike_unit is StrikeUnit.log_moneyness:
            return np.log(strike / forward)
        else:
            raise RuntimeError(f"Unhandled target_strike_unit {target_strike_unit.name}")

    @staticmethod
    def transform_price(strike: ScalarOrArray,
                        strike_unit: StrikeUnit,
                        price: ScalarOrArray,
                        price_unit: PriceUnit,
                        target_price_unit: PriceUnit,
                        expiry: float,
                        discount_factor: float,
                        forward: float) -> ScalarOrArray:
        
        actual_strike = InternalQuoteProcessor.transform_strike(strike=strike, strike_unit=strike_unit, 
                                                                target_strike_unit=StrikeUnit.strike, forward=forward)

        if not isinstance(actual_strike, np.ndarray):  # scalar
            return InternalQuoteProcessor._get_single_price(actual_strike=actual_strike, price=price,
                                                            price_unit=price_unit, target_price_unit=target_price_unit,
                                                            expiry=expiry, discount_factor=discount_factor,
                                                            forward=forward)
        else: 
            target_prices = np.full(shape=actual_strike.shape, fill_value=np.nan)
            for i in range(actual_strike.size):
                target_prices[i] = InternalQuoteProcessor._get_single_price(
                    actual_strike=actual_strike[i], price=price[i], price_unit=price_unit,
                    target_price_unit=target_price_unit,  expiry=expiry, discount_factor=discount_factor,
                    forward=forward)
            
            return target_prices
        
    @staticmethod
    def _get_single_price(actual_strike: float,
                          price: float,
                          price_unit: PriceUnit,
                          target_price_unit: PriceUnit,
                          expiry: float,
                          discount_factor: float,
                          forward: float) -> float:

        if price_unit is target_price_unit:
            return price

        if price_unit is not PriceUnit.call:
            if price_unit in (PriceUnit.vol, PriceUnit.total_var):
                if price_unit is PriceUnit.total_var:  # map to vol
                    price = np.sqrt(price / expiry)

                price = discounted_black(forward=forward, strike=actual_strike, vol=price, expiry=expiry,
                                         discount_factor=discount_factor, call_one_else_put_minus_one=1)
            elif price_unit is PriceUnit.normalized_call:
                zero_strike_call = compute_zero_strike_call_value(discount_factor=discount_factor, forward=forward)
                price *= zero_strike_call

        if target_price_unit is PriceUnit.call:
            return price
        elif target_price_unit in (PriceUnit.vol, PriceUnit.total_var):
            price = implied_vol_for_discounted_option(discounted_option_price=price, forward=forward,
                                                      strike=actual_strike, expiry=expiry,
                                                      discount_factor=discount_factor,
                                                      call_one_else_put_minus_one=1)
            if target_price_unit is PriceUnit.total_var:
                price = (price ** 2) * expiry
        elif target_price_unit is PriceUnit.normalized_call:
            zero_strike_call = compute_zero_strike_call_value(discount_factor=discount_factor, forward=forward)
            price /= zero_strike_call
            
        return price

    def filter(self,
               filter_type: FilterType,
               smoothing_param: Optional[float] = DEFAULT_SMOOTHING_PARAM,
               param_grid: Tuple[float] = DEFAULT_SMOOTHING_PARAM_GRID):

        self.transform_quote_surface(quote_surface=self._quote_surface,
                                     target_price_unit=PriceUnit.normalized_call,
                                     target_strike_unit=StrikeUnit.moneyness,
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
            # todo:  make possible for other expiries too. requires interpolation of zeros + forwards ?
            raise RuntimeError(f"expiry {expiry} not in quote expiries {self._quote_surface.expiries()}", )

        quote_slice = self._quote_surface.get_slice(expiry)

        # map strike to units of quote surface
        transformed_strike = self.transform_strike(strike=strike, strike_unit=strike_unit,
                                                   target_strike_unit=self._quote_surface.strike_unit,
                                                   forward=quote_slice.forward)
        normalized_call_bound = self._compute_normalized_call_bound(expiry=expiry,
                                                                    transformed_strike=transformed_strike,
                                                                    bound_type=bound_type)

        price_bound = self.transform_price(strike=strike, strike_unit=strike_unit, price=normalized_call_bound,
                                           price_unit=PriceUnit.normalized_call, target_price_unit=price_unit,
                                           expiry=expiry, discount_factor=quote_slice.discount_factor,
                                           forward=quote_slice.forward)
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

    @staticmethod
    def transform_quote_surface(quote_surface: QuoteSurface,
                                target_price_unit: PriceUnit,
                                target_strike_unit: StrikeUnit,
                                in_place: bool) -> QuoteSurface:

        if in_place:
            trans_quote_surface = quote_surface
        else:
            trans_quote_surface = deepcopy(quote_surface)

        for qs in trans_quote_surface.slices:
            for q in qs.quotes:
                InternalQuoteProcessor.transform_quote(q=q,
                                                       price_unit=quote_surface.price_unit,
                                                       target_price_unit=target_price_unit,
                                                       strike_unit=quote_surface.strike_unit,
                                                       target_strike_unit=target_strike_unit,
                                                       expiry=qs.expiry,
                                                       discount_factor=qs.discount_factor,
                                                       forward=qs.forward,
                                                       in_place=True)
                
        trans_quote_surface.price_unit = target_price_unit
        trans_quote_surface.strike_unit = target_strike_unit
        return trans_quote_surface

    @staticmethod
    def transform_quote(q: Quote,
                        price_unit: PriceUnit,
                        target_price_unit: PriceUnit,
                        strike_unit: StrikeUnit,
                        target_strike_unit: StrikeUnit,
                        expiry: float,
                        discount_factor: float,
                        forward: float,
                        in_place: bool) -> Quote:

        if price_unit is target_price_unit and strike_unit is target_strike_unit:
            return q

        if in_place:
            trans_q = q
        else:
            trans_q = copy(q)

        actual_strike = InternalQuoteProcessor.transform_strike(trans_q.strike, strike_unit=strike_unit,
                                                                target_strike_unit=StrikeUnit.strike, forward=forward)

        trans_q.strike = InternalQuoteProcessor.transform_strike(strike=actual_strike,
                                                                 strike_unit=StrikeUnit.strike,
                                                                 target_strike_unit=target_strike_unit,
                                                                 forward=forward)
        
        InternalQuoteProcessor._update_price_unit(actual_strike=actual_strike,
                                                  price_unit=price_unit,
                                                  target_price_unit=target_price_unit,
                                                  expiry=expiry,
                                                  discount_factor=discount_factor,
                                                  forward=forward,
                                                  q=trans_q)

        return trans_q

    @staticmethod
    def _update_price_unit(actual_strike: float,
                           price_unit: PriceUnit,
                           target_price_unit: PriceUnit,
                           expiry: float,
                           discount_factor: float,
                           forward: float,
                           q: Quote):

        q.bid = InternalQuoteProcessor.transform_price(strike=actual_strike, strike_unit=StrikeUnit.strike, price=q.bid,
                                                       price_unit=price_unit, target_price_unit=target_price_unit,
                                                       expiry=expiry, discount_factor=discount_factor, forward=forward)
        q.ask = InternalQuoteProcessor.transform_price(strike=actual_strike, strike_unit=StrikeUnit.strike, price=q.ask,
                                                       price_unit=price_unit, target_price_unit=target_price_unit,
                                                       expiry=expiry, discount_factor=discount_factor, forward=forward)
