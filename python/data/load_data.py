"""  This module contains the function allows for loading data sets using get_data_set. """

import os
import numpy as np
import pandas as pd
from enum import Enum
from typing import Optional, Tuple, final
import qproc
from qproc import PriceUnit

DAX_EXPIRY_DAYS: final = [3, 28, 48, 68, 133, 198, 263, 398]
DAX_SPOT: final = 7268.91


class DataSetName(Enum):
    na = 0
    example_data_afop = 1
    spx500_5_feb_2018 = 2
    tsla_15_jun_2018 = 3
    dax_13_jun_2000 = 4


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

    def unique_expiries(self) -> np.ndarray:
        return np.unique(self.expiries)



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
    elif ds_name is DataSetName.dax_13_jun_2000:
        return get_dax_ds()
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


def get_dax_ds() -> OptionDataSet:
    vols, strikes, expiries = _get_dax_vols_strikes_expiries()
    rates = _get_raw_data_set("zero_rates_euribor_13_jun_2000.csv", index_col=None)["zero_rate"].values

    annualized_expiries_in_years = np.array(DAX_EXPIRY_DAYS) / qproc.CALENDAR_DAYS_YEAR
    forwards = DAX_SPOT * np.exp(rates * annualized_expiries_in_years)

    return OptionDataSet(option_prices=vols,
                         price_unit=PriceUnit.vol,
                         strikes=strikes,
                         expiries=expiries,
                         forwards=forwards,
                         rates=rates,  # rate not given
                         name=DataSetName.dax_13_jun_2000)


def _get_dax_vols_strikes_expiries() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    df = _get_raw_data_set("dax_vol_surface_13_jun_2000.csv", index_col=None)
    strikes_series = df['strike']
    strikes = []
    vols = []
    expiries = []
    for d in DAX_EXPIRY_DAYS:
        colname = str(d)
        df_d = df[colname]
        non_nan_indices = df_d.notnull()

        vols_d = df_d[non_nan_indices].values
        vols.append(vols_d)

        strikes_d = strikes_series[non_nan_indices].values
        strikes.append(strikes_d)

        expiries.append(np.full(shape=vols_d.shape, fill_value=d / qproc.CALENDAR_DAYS_YEAR))

    vols = np.concatenate(vols) / 100.0  # the vols are given in percentage
    strikes = np.concatenate(strikes)
    expiries = np.concatenate(expiries)
    return vols, strikes, expiries


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
