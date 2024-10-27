""" This module collects the exposed types from the package. """

from abc import ABC, abstractmethod
from computils import ScalarOrArray
from qproc import StrikeUnit, PriceUnit


class VolSurface(ABC):

    @abstractmethod
    def calibrate(self):
        """ Calibrates the volatility surface object to the given option price data.

        :return:
        """

    @abstractmethod
    def get_price(self,
                  price_unit: PriceUnit,
                  expiry: float,
                  strike: ScalarOrArray,
                  strike_unit: StrikeUnit = StrikeUnit.strike) -> ScalarOrArray:
        """ Returns the option price for given expiry and strike(s) in the requested unit.

        :param price_unit:
        :param expiry:
        :param strike: scalar or (n,) array of strikes.
        :param strike_unit: optional, if None the strike unit of the
        :return: prices: an object with prices for each given strike that is of the same type and dimension as strike.
        """

    @abstractmethod
    def compute_risk_neutral_density(self,
                                     expiry: float,
                                     x: ScalarOrArray) -> ScalarOrArray:
        """ Computes the risk-neutral density for values of the underlying asset at expiry.

        :param expiry:
        :param x: value(s) of the underlying asset at expiry for which to compute the risk-neutral density.
        :return: risk-neutral density values: an object of the same time and dimension as x.
        """

    @abstractmethod
    def compute_risk_neutral_cdf(self,
                                 expiry: float,
                                 x: ScalarOrArray) -> ScalarOrArray:
        """ Computes the risk-neutral cumulative distribution function (CDF) for values of the underlying asset at
        expiry.

        :param expiry:
        :param x: value(s) of the underlying asset at expiry for which to compute the risk-neutral density.
        :return: risk-neutral CDF values: an object of the same time and dimension as x.
        """
