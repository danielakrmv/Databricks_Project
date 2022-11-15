import logging

import pyspark.sql.functions as f
from pyspark.sql import DataFrame
from pyspark.sql.types import FloatType

from uapc_aiacad.common.validation import Validator

logger = logging.getLogger(__name__)


def find_sum_quantity_per_certain_date(df: DataFrame, group_col: str, sum_col: str, unit_of_measure: str) -> DataFrame:
    """
    The function returns new df with data per unit or weight, grouping by date col and sum quantity per this date
    Args:
        df: DataFrame
        group_col: str
        sum_col: str
        unit_of_measure: str, can be per unit (ST) or weight (KG)
    Returns:
        df: DataFrame оf quantities relative to the unit of measure for the specific date, if unit of measure is not
        valid raise an ValueError
    """
    Validator.raise_if_unit_of_measure_is_not_valid(unit_of_measure)

    daily_distribute_quantity = Validator.return_concrete_string_to_the_unit_of_measure(unit_of_measure=unit_of_measure)

    df = (df
          .filter(f.col("einh_id") == unit_of_measure)
          .groupBy(group_col)
          .sum(sum_col)
          .withColumnRenamed(f'sum(menge)', daily_distribute_quantity))
    return df


def create_column_with_names_of_the_days(df: DataFrame, column: str) -> DataFrame:
    """
        Creating new column with the converted date to week name day - Mon, Tue, Wed, etc.
        Args:
            df: DataFrame
            column: date column
        Returns:
            df: DataFrame with new column
    """
    return df.withColumn('day_name', f.date_format(column, 'E'))


def create_column_with_num_represent_the_days(df: DataFrame, column: str) -> DataFrame:
    """
        Creating new column with the converted date to the day number in the week
        Args:
            df: DataFrame
            column: date column
        Returns:
            df: DataFrame with new column
    """
    return df.withColumn('day_of_week', ((f.dayofweek(column) + 5) % 7) + 1)


def creating_df_with_min_and_max_daily_distributed_quantity_per_unit_in_thsd(df: DataFrame):
    """
        Grouping by converted day_of_week and day_name columns and creating new columns with max and min daily
        quantity per unit in their real values and columns with max and min daily quantity per unit
        in thousands for better illustration after.
        Args:
            df: DataFrame
        Returns:
            df: DataFrame with new columns, sorted by day of the week
    """

    daily_distribution_df_per_unit = (df.groupBy("day_of_week", "day_name")
                                      .agg(f.max(f"daily_distribute_quantity_per_unit").alias("max_daily_quantity_per_unit"),
                                           f.min("daily_distribute_quantity_per_unit").alias(f"min_daily_quantity_per_unit"))
                                      .withColumn("max_daily_quantity_per_unit_in_thousand",
                                                  (f.col('max_daily_quantity_per_unit') / 1000))
                                      .withColumn(f"min_daily_quantity_per_unit_in_thousand",
                                                  (f.col(f'min_daily_quantity_per_unit') / 1000))
                                      .withColumn("max_daily_quantity_per_unit_in_thousand",
                                                  f.round(f.col("max_daily_quantity_per_unit_in_thousand"), 2))
                                      .withColumn("min_daily_quantity_per_unit_in_thousand",
                                                  f.round(f.col("min_daily_quantity_per_unit_in_thousand"), 2))
                                      .withColumn("max_daily_quantity_per_unit_in_thousand",
                                                  f.col("max_daily_quantity_per_unit_in_thousand").cast(FloatType()))
                                      .withColumn("min_daily_quantity_per_unit_in_thousand",
                                                  f.col("min_daily_quantity_per_unit_in_thousand").cast(FloatType())))

    daily_distribution_df_per_unit = daily_distribution_df_per_unit.sort('day_of_week')
    return daily_distribution_df_per_unit


def creating_df_with_min_and_max_daily_distributed_quantity_per_weight(df: DataFrame):
    """
        Grouping by converted day_of_week and day_name columns and creating new columns with max and min daily
        quantity per weight in their real values.
        Args:
            df: DataFrame
        Returns:
            df: DataFrame with new columns, sorted by day of the week
    """

    daily_distribution_df_quantity_per_weight = (df.groupBy("day_of_week", 'day_name')
                                                 .agg(f.max("daily_distribute_quantity_per_weight").alias("max_daily_quantity_per_weight"),
                                                      f.min("daily_distribute_quantity_per_weight").alias("min_daily_quantity_per_weight"))
                                                 .withColumn("max_daily_quantity_per_weight",
                                                             f.col(f"max_daily_quantity_per_weight").cast(FloatType()))
                                                 .withColumn("min_daily_quantity_per_weight",
                                                             f.col(f"min_daily_quantity_per_weight").cast(FloatType())))

    daily_distribution_df_quantity_per_weight = daily_distribution_df_quantity_per_weight.sort('day_of_week')
    return daily_distribution_df_quantity_per_weight


def do_transform_per_unit_of_measure(df: DataFrame, unit_of_measure: str):
    """
        Relative to the specified unit of measure, returns the specific function
        Args:
            df: DataFrame
            unit_of_measure: str
        Returns:
            df: DataFrame
    """
    Validator.raise_if_unit_of_measure_is_not_valid(unit_of_measure=unit_of_measure)
    if unit_of_measure == "ST":
        return creating_df_with_min_and_max_daily_distributed_quantity_per_unit_in_thsd(df=df)
    elif unit_of_measure == "KG":
        return creating_df_with_min_and_max_daily_distributed_quantity_per_weight(df=df)


def convert_to_pandas(df: DataFrame):
    """
        Converts PySpark DF to pandas.DataFrame
        Args:
            df: iterable[pyspark.DataFrame], all read dataframes
        Returns:
            pandas.DataFrame
    """
    return df.toPandas()


def convert_to_pandas_type(df: DataFrame, columns_to_convert: list, type_pd: str):
    """
        Converts columns to certain pandas type
        Args:
            df: pandas.DataFrame
            columns_to_convert: List[str], columns to be converted to concrete pd type\
            type_pd: pandas data type
        Returns:
            pandas.DataFrame
    """

    for col in columns_to_convert:
        df[col] = df[col].astype(type_pd)

    return df