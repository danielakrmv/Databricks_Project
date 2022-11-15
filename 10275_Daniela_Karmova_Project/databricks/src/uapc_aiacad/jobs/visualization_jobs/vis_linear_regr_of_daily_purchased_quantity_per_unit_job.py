import logging
from uapc_aiacad.common.abstract_job import AbstractPredictJob
from uapc_aiacad.transformations.get_daily_distribute_quantity_per_unit_and_weight_transformation import *
from uapc_aiacad.visualization.visualization_transformation import *
from uapc_aiacad.common.validation import Validator

logger = logging.getLogger(__name__)

format = "delta"
date_col = "k_bon_dat"
quantity_col = "menge"
unit_of_measure = "ST"

columns_to_convert_to_pandas_dtypes = ["max_daily_quantity_per_unit",
                                       "min_daily_quantity_per_unit",
                                       "max_daily_quantity_per_unit_in_thousand",
                                       "min_daily_quantity_per_unit_in_thousand"]


class VisDailyDistributedQuantityPerUnitPredictJob(AbstractPredictJob):

    def run(self):
        read_dfs = self._extract()
        result_to_vis_dfs = self._transform(read_dfs)
        self._visualize_prediction_plot(result_to_vis_dfs)

    def _extract(self):
        logger.info("Starting load the data")
        logger.info("output_file_with_df_with_correct_bon_ids_and_names_of_art = %s",
                    self.config["databricks"]["data"]["output_file_with_filtered_sales_ds"])

        Validator.raise_if_format_type_is_not_valid(format)

        try:
            filtered_df_sales = self.spark.read.format(format)\
                .load(self.config["databricks"]["data"]["output_file_with_filtered_sales_ds"])
        except ValueError as error:
            logger.error("Invalid path to dataset!")
            raise ValueError("Invalid path to dataset!", str(error))

        logger.info('Successfully open the input files')
        return filtered_df_sales

    def _transform(self, read_dfs):

        filtered_df_sales = read_dfs
        logger.info("Doing transformations...")

        logger.info("Creating new df with grouped date of my period"
                    "and find max and min daily distributed quantity per concrete unit of measure - in this case 'ST'")

        filtered_df_sales_quantity_per_unit = find_sum_quantity_per_certain_date(df=filtered_df_sales,
                                                                                 group_col=date_col,
                                                                                 sum_col=quantity_col,
                                                                                 unit_of_measure=unit_of_measure)

        logger.info("Creating new column with the converted date to week name day - Mon, Tue, Wed, etc.")
        total_amount_df = create_column_with_names_of_the_days(df=filtered_df_sales_quantity_per_unit,
                                                               column=date_col)

        logger.info("Creating new column with the converted date to the day number in the week - from 1 to 7")
        total_amount_df = create_column_with_num_represent_the_days(df=total_amount_df,
                                                                    column=date_col)

        logger.info("Grouping by converted day_of_week and day_name columns "
                    "and creating new columns with max and min daily quantity per unit in their real values "
                    "and columns with max and min daily quantity per unit in thousands for better illustration after.")

        daily_distribution_df_quantity_per_unit = convert_to_pandas(do_transform_per_unit_of_measure(df=total_amount_df,
                                                                                                     unit_of_measure=unit_of_measure))
        logger.info("Successfully converted pyspark df to pandas dataframe")

        logger.info("Convert concrete columns from daily_distribution_df_quantity_per_unit df to pandas type")
        daily_distribution_df_quantity_per_unit = convert_to_pandas_type(df=daily_distribution_df_quantity_per_unit,
                                                                         columns_to_convert=columns_to_convert_to_pandas_dtypes,
                                                                         type_pd="float64")

        logger.info("Successfully converted df columns to concrete pandas type.")

        return daily_distribution_df_quantity_per_unit

    def _visualize_prediction_plot(self, result_to_vis_dfs):

        daily_distribution_df_quantity_per_unit = result_to_vis_dfs
        logger.info("Visualize linear regression...")

        draw_linear_regression_for_daily_purchased_quantity(df=daily_distribution_df_quantity_per_unit,
                                                            x_axis_column="day_of_week",
                                                            y_axis_column="min_daily_quantity_per_unit_in_thousand",
                                                            top="min",
                                                            unit_of_measure=unit_of_measure)

        logger.info("Successfully visualized linear regression for min daily quantities per unit!")

        draw_linear_regression_for_daily_purchased_quantity(df=daily_distribution_df_quantity_per_unit,
                                                            x_axis_column="day_of_week",
                                                            y_axis_column="max_daily_quantity_per_unit_in_thousand",
                                                            top="max",
                                                            unit_of_measure=unit_of_measure)

        logger.info("Successfully visualized linear regression for max daily quantities per unit!")