""" This module collects all types from the arbitrage_filter package. """

from abc import ABC, abstractmethod


class ArbitrageFilter(ABC):
    @abstractmethod
    def filter(self):
        """ Filters the quote surface passed to the filter. """

    @abstractmethod
    def compute_lower_bound(self,
                            expiry: float,
                            trans_strike: float) -> float:
        """ Computes the lower bound implied by the quotes for the given expiry and transformed strike.

        :param expiry:
        :param trans_strike: must have the same strike unit as the underlying quote surface on which the filtering
            algorithm is applied (e.g., moneyness for European call options).
        :return: lower_bound
        """

    @abstractmethod
    def compute_upper_bound(self,
                            expiry: float,
                            trans_strike: float) -> float:
        """ Computes the upper bound implied by the quotes for the given expiry and transformed strike.

        :param expiry:
        :param trans_strike: must have the same strike unit as the underlying quote surface on which the filtering
            algorithm is applied (e.g., moneyness for European call options).
        :return: upper_bound
        """
