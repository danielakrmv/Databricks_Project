# Validation class with static methods
import logging

logger = logging.getLogger(__name__)

from pyspark.sql import DataFrame


class Validator:
    @staticmethod
    def raise_if_format_type_is_not_valid(format_type: str):
        """The function returns boolean expression

            Args:
                format_type: str

            Returns:
                bool: True if format_type is right

        """
        if not format_type == 'delta':
            logger.error("Invalid format! The dataset you want to read is format 'delta'")
            raise ValueError("Invalid format! The dataset you want to read is format 'delta'")

    @staticmethod
    def raise_if_unit_of_measure_is_not_valid(unit_of_measure: str):
        """The function raise ValueError if unit_of_measure is not valid

            Args:
                unit_of_measure: str

            Returns:
                raise an error if unit of measure is invalid type
        """
        valid_unit_of_measure = ["KG", "ST"]

        if unit_of_measure not in valid_unit_of_measure:
            logger.error("Unit of measure can be only 'KG' or 'ST'!")
            raise ValueError("Unit of measure can be only 'KG' or 'ST'!")

    @staticmethod
    def raise_if_len_of_old_columns_name_is_different_from_len_of_new_columns_names(df: DataFrame, new_names: list):
        """The function raise ValueError if old_names of articles is different from the new names

                Args:
                    df: DataFrame
                    new_names: list, contain new names of columns

                Returns:
                    raise an error if len of old names is different 
        """
        old_names = df.columns

        if len(old_names) != len(new_names):
            logger.error(f"The length of the {old_names} and {new_names} lists should be the same.")
            raise ValueError(f"The length of the {old_names} and {new_names} lists should be the same.")

    @staticmethod
    def return_concrete_string_to_the_unit_of_measure(unit_of_measure: str) -> str:
        """The function raise ValueError if unit of measure is invalid type or return certain 
        variable depending on the unit type

                Args:
                    unit_of_measure: str, can be 'ST' or 'KG'

                Returns:
                    str
                    raise an error if len of old names is different 
        """
        daily_distribute_quantity_per_unit = 'daily_distribute_quantity_per_unit'
        daily_distribute_quantity_per_weight = 'daily_distribute_quantity_per_weight'

        if unit_of_measure == "ST":
            return daily_distribute_quantity_per_unit
        elif unit_of_measure == "KG":
            return daily_distribute_quantity_per_weight
        else:
            raise ValueError("Invalid unit of measure!")
