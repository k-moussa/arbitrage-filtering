""" This module collects several types for storing quotes. """

import bisect
import numpy as np
from typing import Optional, List
from ..globals import Side, StrikeUnit, PriceUnit


class Quote:
    def __init__(self,
                 bid: float,
                 ask: float,
                 strike: float,
                 liq_proxy: float):

        self.bid = bid
        self.ask = ask
        self.strike = strike
        self.liq_proxy = liq_proxy

    def __lt__(self, rhs):  # < operator
        """ Overloads the < operator to allow for using the bisection module for efficient insertion and
        lookup based on the strike. """

        return self.strike < rhs.strike

    def __eq__(self, rhs):  # == operator
        """ Overloads the == operator to allow for using the bisection module for efficient insertion and
            lookup based on the strike. """

        return self.strike == rhs.strike

    def __call__(self, side: Side) -> float:
        if side is Side.mid:
            is_mid_quote = self.bid == self.ask
            if is_mid_quote:
                return self.bid
            else:
                return (self.bid + self.ask) / 2.0
        elif side is Side.bid:
            return self.bid
        else:
            return self.ask

    def set_price(self,
                  price: float,
                  side: Side):

        if side is Side.mid:
            self.bid = self.ask = price
        elif side is Side.bid:
            self.bid = price
        else:
            self.ask = price

    def get_transformed_strike(self,
                               strike_unit: StrikeUnit,
                               forward: Optional[float] = None) -> float:

        if strike_unit is StrikeUnit.strike:
            return self.strike
        elif strike_unit in [StrikeUnit.moneyness, StrikeUnit.log_moneyness]:
            if forward is None:
                raise RuntimeError(f"strike_unit {strike_unit.name} requires passing the forward.")

            moneyness = self.strike / forward
            if strike_unit is StrikeUnit.moneyness:
                return moneyness
            else:
                return np.log(moneyness)
        else:
            raise RuntimeError(f"unhandled strike_unit {strike_unit.name}.")


class QuoteSlice:
    def __init__(self,
                 forward: float,
                 rate: float,
                 expiry: float):

        self.expiry: float = expiry
        self.forward: float = forward
        self.discount_factor: float = np.exp(-rate * expiry)
        self.quotes: List[Quote] = []

    def add_quote(self, q: Quote):
        bisect.insort_left(self.quotes, q)

    def n_quotes(self) -> int:
        return len(self.quotes)


class QuoteSurface:
    def __init__(self,
                 price_unit: PriceUnit,
                 strike_unit: StrikeUnit):

        self.price_unit: PriceUnit = price_unit
        self.strike_unit: StrikeUnit = strike_unit
        self.slices: List[QuoteSlice] = []

    def add_slice(self, quote_slice: QuoteSlice):
        self.slices.append(quote_slice)

    def n_expiries(self) -> int:
        return len(self.slices)

    def n_quotes(self) -> int:
        total_n_quotes = 0
        for qs in self.slices:
            total_n_quotes += qs.n_quotes()

        return total_n_quotes