""" This module collects all types from the arbitrage_filter package. """

from abc import ABC, abstractmethod


class ArbitrageFilter(ABC):
    @abstractmethod
    def filter(self):
        """ Filters the quote surface passed to the filter. """
