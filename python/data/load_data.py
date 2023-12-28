"""  This module contains the function allows for loading data sets using get_data_set. """

import os
import numpy as np
import pandas as pd
from enum import Enum
from typing import Optional
from qproc import PriceUnit


class DataSetName(Enum):
    na = 0
    example_data_afop = 1
    spx500_5_feb_2018 = 2
    tsla_15_jun_2018 = 3


class OptionDataSet:
    def __init__(self,
                 option_prices: np.ndarray,
                 price_unit: PriceUnit,
                 strikes: np.ndarray,
                 expiries: np.ndarray,
                 forwards: np.ndarray,
                 rates: np.ndarray,
                 liquidity_proxies: Optional[np.ndarray] = None,
                 name: DataSetName = DataSetName.na):

        self.option_prices: np.ndarray = option_prices
        self.price_unit: PriceUnit = price_unit
        self.strikes: np.ndarray = strikes
        self.expiries: np.ndarray = expiries
        self.forwards: np.ndarray = forwards
        self.rates: np.ndarray = rates
        self.liquidity_proxies: Optional[np.ndarray] = liquidity_proxies
        self.name: DataSetName = name


def get_option_data(ds_name: DataSetName) -> OptionDataSet:
    """ This function returns a data set of choice.

    :param ds_name:
    :return:
    """

    if ds_name is DataSetName.example_data_afop:
        return get_example_data_afop()
    elif ds_name is DataSetName.spx500_5_feb_2018:
        return get_spx500_ds()
    elif ds_name is DataSetName.tsla_15_jun_2018:
        return get_tsla_ds()
    else:
        raise RuntimeError(f"get_data_set not implemented for data_set_name {ds_name.name}.")


def get_example_data_afop() -> OptionDataSet:
    df = _get_raw_data_set("example_data_afop.csv", index_col=None)
    return OptionDataSet(option_prices=df['call_price'].values,
                         price_unit=PriceUnit.call,
                         strikes=df['strike'].values,
                         expiries=df['expiry'].values,
                         forwards=np.ones((2,)),
                         rates=np.zeros((2,)),
                         name=DataSetName.example_data_afop)


def get_spx500_ds() -> OptionDataSet:
    df = _get_raw_data_set("spx500_5_feb_2018.csv", index_col=None)
    strikes = df['strike'].values
    return OptionDataSet(option_prices=df['vol'].values,
                         price_unit=PriceUnit.vol,
                         strikes=strikes,
                         expiries=np.array([0.082192] * strikes.size),
                         forwards=np.array([2629.80]),
                         rates=np.array([0.97/100.0]),
                         name=DataSetName.spx500_5_feb_2018)


def get_tsla_ds() -> OptionDataSet:
    df = _get_raw_data_set("tsla_15_jun_2018.csv", index_col=None)
    strikes = df['strike'].values
    return OptionDataSet(option_prices=df['vol'].values,
                         price_unit=PriceUnit.vol,
                         strikes=strikes,
                         expiries=np.array([1.59178] * strikes.size),
                         forwards=np.array([356.73]),
                         rates=np.array([0.0]),  # rate not given
                         name=DataSetName.tsla_15_jun_2018)


def _get_raw_data_set(file_name: str,
                      index_col: int = None,
                      parse_dates: bool = True) -> pd.DataFrame:
    """ Returns the raw data set for given file name.

    :param file_name: name of the file, including extension.
    :param index_col: column of data to use as index labels.
    :param parse_dates: bool determining whether or not to parse dates. Can be set to False if the data set is
                        very large and only a subset is needed.
    :return: raw_data: a pd df with the raw data.
    """

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "data_sets", file_name)

    if ".csv" in file_name:
        raw_data = pd.read_csv(file_path, index_col=index_col, parse_dates=parse_dates, infer_datetime_format=True)
    else:
        raise RuntimeError("Unsupported file format {:s}".format(file_name))

    return raw_data
