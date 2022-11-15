import logging

import pyspark.sql.functions as f
from datetime import timedelta, datetime, date
from pyspark.sql import DataFrame
from pyspark.sql.types import FloatType

from uapc_aiacad.common.validation import Validator

logger = logging.getLogger(__name__)


def select_columns(df: DataFrame, *columns) -> DataFrame:
    """The function returns only selected columns from DataFrame

        Args:
          df: DataFrame
          columns: args: Needed columns to select (can be one or many)

        Returns:
          df: DataFrame: DataFrame with selected columns

    """
    return df.select([col for col in columns])


def take_date_weeks_before_current_date(weeks_period: int) -> date:
    """
        Return the current local date minus the set weeks_period
        Args:
            weeks_period:int,  set weeks_period as int, must be positive or zero, else return current date
        Returns:
            datetime: datetime object shows date n days before current one
    """
    if weeks_period <= 0:
        return datetime.now().date()

    return datetime.now().date() - timedelta(weeks=weeks_period)


def get_needed_data_for_curr_period(df: DataFrame, date_column: str, period_in_weeks: int) -> DataFrame:
    """
       PySpark DF filter by date the last n weeks, today is excluded
       Args:
           df: DataFrame, input df
           date_column: str, the column name that will be used to filter
           period_in_weeks: int, weeks, must be positive or zero, else return the initial df
       Returns:
           DataFrame: contains only data for the last n weeks, if df is not valid raise an exception
    """

    today_date = datetime.now().date()
    end_date = today_date - timedelta(days=1)
    start_date = take_date_weeks_before_current_date(period_in_weeks)

    if df is not None:
        return df.where((f.col(date_column) >= start_date) & (f.col(date_column) <= end_date))
    else:
        logger.error("NoneType object has no attribute 'where'!")
        raise AttributeError("NoneType object has no attribute 'where'!")


def get_correct_bon_id(df: DataFrame, column: str) -> DataFrame:
    """
        PySpark DF with bon_id's where count bon_zeile is equal max bon_zeile per one bon_id and count bon_id's
        is equal count bon_zeile
        Args:
            df: DataFrame
            column: str, the column name that will be used to filter
        Returns:
            DataFrame: contains only correct bon_id's
    """

    correct_df = (df.groupby(df[column])
                  .agg(f.max("bon_zeile").alias('max_bon_zeile'), f.count("bon_id").alias("count_bon_id"),
                       f.count("bon_zeile").alias("count_bon_zeile"))
                  .filter((f.col("max_bon_zeile") == f.col("count_bon_id")) & (f.col("count_bon_id") == f.col("count_bon_zeile"))))

    return correct_df


def joining_df(df1: DataFrame, df2: DataFrame, column: str, way_to_join: str) -> DataFrame:
    """
        New joined PySpark DF
        Args:
            df1: left DataFrame
            df2: right DataFrame
            column: str, the column name that will be used to do joining
            way_to_join: str, the way we want to join two df
        Returns:
            df: DataFrame: new merged df
    """
    new_df = df1.join(df2, column, how=way_to_join)
    return new_df


def get_data_per_unit_of_measure(df: DataFrame, column_to_filter: str, column_to_group_by: str,  unit_of_measure: str) -> DataFrame:
    """
        The function returns new df with data per unit or weight
        Args:
            df: DataFrame
            column_to_filter: str
            column_to_group_by: str
            unit_of_measure: str, can be per unit (ST) or weight (KG)
        Returns:
            df: DataFrame per unit of measure, if unit of measure is not valid raise an Exception
    """
    Validator.raise_if_unit_of_measure_is_not_valid(unit_of_measure)

    df_per_unit_measure = (df
                           .filter(f.col(column_to_filter) == unit_of_measure)
                           .groupBy(column_to_group_by)
                           .agg(f.sum('menge').alias(f"Total Menge per one art_id {unit_of_measure}"))
                           .filter(f.col(f"Total Menge per one art_id {unit_of_measure}") >= '0.01')
                           # In order to edit the difference between the historical and the corresponding order
                           # of the initial marking of the product
                           .withColumn(f"Total Menge per one art_id {unit_of_measure}",
                                       f.round(f.col(f"Total Menge per one art_id {unit_of_measure}"), 2))
                           .withColumn(f"Total Menge per one art_id {unit_of_measure}",
                                       f.col(f"Total Menge per one art_id {unit_of_measure}")
                                       .cast(FloatType()))
                           )

    return df_per_unit_measure


def filter_data(df: DataFrame, column: str, filter_by: str):
    """
        PySpark DF with filtered column
        Args:
            df: DataFrame
            column: str, the column name that will be used to filter
            filter_by: str, column to filter by
        Returns:
            df: DataFrame: filtered DF
    """
    return df.filter(f.col(column) == filter_by)


def sorting_data_asc(df: DataFrame, column_to_sort: list) -> DataFrame:
    """
        PySpark DF with sorted data in ascending order
        We can sort the df by one or many column
        Args:
            df: DataFrame
            column_to_sort: str, the column name that will be used to sort
        Returns:
            df: DataFrame: sorted DF
    """
    if len(column_to_sort) == 1:
        return df.sort(f.col(column_to_sort[0]).asc()).limit(10)
    return df.sort(f.col(column_to_sort[0]).asc(), f.col(column_to_sort[1]).asc())


def sorting_data_desc(df: DataFrame, column_to_sort: list) -> DataFrame:
    """
           PySpark DF with sorted data in descending order
           We can sort the df by one or many column
           Args:
               df: DataFrame
               column_to_sort: str, the column name that will be used to sort
           Returns:
               df: DataFrame: sorted DF
       """
    if len(column_to_sort) == 1:
        return df.sort(f.col(column_to_sort[0]).desc()).limit(10)
    return df.sort(f.col(column_to_sort[0]).desc(), f.col(column_to_sort[1]).desc())


def rename_column(df: DataFrame, new_names: list):
    """
        The function can be used to rename the column names of the df
        Args:
            df: DataFrame: df with old column names
            new_names: list, contains the new names that we want to apply
        Returns:
            df: DataFrame: df with new column names, if len of old names is different
            from len of new names raise an exception
    """
    Validator.raise_if_len_of_old_columns_name_is_different_from_len_of_new_columns_names(df, new_names)
    old_names = df.columns

    for old, new in zip(old_names, new_names):
        df = df.withColumnRenamed(old, new)

    return df


def drop_columns(df: DataFrame, columns: list) -> DataFrame:
    """
    The function can be used to drop columns we don't need
    Args:
        df: DataFrame: df with old column names
        columns: list
    Returns:
        df: DataFrame: df with dropped columns
    """

    return df.drop(*columns)


def display_df(df: DataFrame):
    """
    The function only display current df
    Args:
        df: DataFrame
        Returns:
            None-Type object vis.
    """
    return df.display()