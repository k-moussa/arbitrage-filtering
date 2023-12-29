""" This module implements the InternalQuoteProcessor class. """

from copy import copy, deepcopy
from ..globals import *
from .filter_factory import create_filter
from .quote_structures import Quote, QuoteSurface
from .volatility_functions import implied_vol_for_discounted_option, discounted_black
from .zero_strike_computation import compute_zero_strike_call_value

COL_NAMES: final = (EXPIRY_KEY, STRIKE_KEY, MID_KEY, BID_KEY, ASK_KEY, LIQ_KEY)


class InternalQuoteProcessor(OptionQuoteProcessor):
    def __init__(self, quote_surface: QuoteSurface):
        self._quote_surface: QuoteSurface = quote_surface

    @staticmethod
    def get_transformed_strike(strike: ScalarOrArray,
                               strike_unit: StrikeUnit,
                               forward: float) -> ScalarOrArray:

        if strike_unit is StrikeUnit.strike:
            return strike
        elif strike_unit is StrikeUnit.moneyness:
            return strike / forward
        elif strike_unit is StrikeUnit.log_moneyness:
            return np.log(strike / forward)
        else:
            raise RuntimeError(f"Unhandled strike_unit {strike_unit.name}")

    @staticmethod
    def get_price(strike: ScalarOrArray,
                  price: ScalarOrArray,
                  price_unit: PriceUnit,
                  target_price_unit: PriceUnit,
                  expiry: float,
                  discount_factor: float,
                  forward: float) -> ScalarOrArray:
        
        if not isinstance(strike, np.ndarray):  # scalar
            return InternalQuoteProcessor._get_single_price(strike=strike, price=price, price_unit=price_unit,
                                                            target_price_unit=target_price_unit, expiry=expiry,
                                                            discount_factor=discount_factor, forward=forward)
        else: 
            target_prices = np.full(shape=strike.shape, fill_value=np.nan)
            for i in range(strike.size):
                target_prices[i] = InternalQuoteProcessor._get_single_price(
                    strike=strike[i], price=price[i], price_unit=price_unit, target_price_unit=target_price_unit, 
                    expiry=expiry, discount_factor=discount_factor, forward=forward)
            
            return target_prices
        
    @staticmethod
    def _get_single_price(strike: float,
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

                price = discounted_black(forward=forward, strike=strike, vol=price, expiry=expiry,
                                         discount_factor=discount_factor, call_one_else_put_minus_one=1)
            elif price_unit is PriceUnit.normalized_call:
                zero_strike_call = compute_zero_strike_call_value(discount_factor=discount_factor, forward=forward)
                price *= zero_strike_call

        if target_price_unit is PriceUnit.call:
            return price
        elif target_price_unit in (PriceUnit.vol, PriceUnit.total_var):
            price = implied_vol_for_discounted_option(discounted_option_price=price, forward=forward,
                                                      strike=strike, expiry=expiry,
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

        arbitrage_filter = create_filter(quote_surface=self._quote_surface,
                                         filter_type=filter_type,
                                         smoothing_param=smoothing_param,
                                         smoothing_param_grid=param_grid)
        arbitrage_filter.filter()

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

        actual_strike = InternalQuoteProcessor._get_actual_strike(trans_q.strike, strike_unit=strike_unit,
                                                                  forward=forward)

        trans_q.strike = InternalQuoteProcessor.get_transformed_strike(strike=actual_strike,
                                                                       strike_unit=target_strike_unit,
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
    def _get_actual_strike(transformed_strike: float,
                           strike_unit: StrikeUnit,
                           forward: float) -> float:
        """ Returns the actual strike for a given transformed strike. """

        if strike_unit is not StrikeUnit.strike:  # map to strike
            if strike_unit is StrikeUnit.moneyness:
                transformed_strike *= forward
            elif strike_unit is StrikeUnit.log_moneyness:
                transformed_strike = np.exp(transformed_strike) * forward
            else:
                raise RuntimeError(f"Unhandled strike_unit {strike_unit.name}")

        return transformed_strike

    @staticmethod
    def _update_price_unit(actual_strike: float,
                           price_unit: PriceUnit,
                           target_price_unit: PriceUnit,
                           expiry: float,
                           discount_factor: float,
                           forward: float,
                           q: Quote):

        q.bid = InternalQuoteProcessor.get_price(strike=actual_strike, price=q.bid,  price_unit=price_unit,
                                                 target_price_unit=target_price_unit, expiry=expiry,
                                                 discount_factor=discount_factor, forward=forward)
        q.ask = InternalQuoteProcessor.get_price(strike=actual_strike, price=q.ask, price_unit=price_unit,
                                                 target_price_unit=target_price_unit, expiry=expiry,
                                                 discount_factor=discount_factor, forward=forward)
