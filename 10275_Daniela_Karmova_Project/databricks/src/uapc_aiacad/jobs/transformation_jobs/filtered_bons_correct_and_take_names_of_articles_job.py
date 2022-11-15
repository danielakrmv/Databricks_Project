import logging

from uapc_aiacad.common.abstract_job import AbstractEtlJob
from uapc_aiacad.transformations.get_most_purchased_and_less_purchased_articles_per_unit_of_measure import *
from uapc_aiacad.common.validation import Validator

logger = logging.getLogger(__name__)

# format type
format = "delta"

# period to filter data
period_in_weeks = 5

# date_column
start_date_col = "k_bon_dat"

# columns for aggregating and filtering
useful_columns_from_sales_df = {
    "bons_column": "bon_id",
    "bon_line_col": "bon_zeile",
    "article_id": "kl_art_id",
    "quantity_col": "menge",
    "unit_of_measure_col": "einh_id",
    "aktion_flag": "aktion_fg",
    "start_date_col": "k_bon_dat"
}

column_to_select_from_ds_with_german_art_names = {
    "names_of_articles_gm": "kl_art_bez",
    "article_id": "kl_art_id",
    "column_to_join_by": "art_id",
    "group_names": "wug_bez"
}

column_to_select_from_ds_with_bg_art_names = {
    "id_for_bg_names": "spr_id",
    "art_name_bg_col": "art_bez",
    "column_to_join_by": "art_id"
}


class GetFilteredSalesDFEtlJob(AbstractEtlJob):
    def _extract(self):
        logger.info("Starting finding articles")
        logger.info("input_dataset_sales_file  = %s", self.config["databricks"]["data"]["input_file_sales"])
        logger.info("input_dataset_art_hier_file  = %s", self.config["databricks"]["data"]["input_file_german_art_names"])
        logger.info("input_dataset_art_bg_names_file  = %s",
                    self.config["databricks"]["data"]["input_file_articles_with_bg_names"])
        logger.info("output_file_with_df_with_correct_bon_ids_and_names_of_art = %s",
                    self.config["databricks"]["data"]["output_file_with_filtered_sales_ds"])

        Validator.raise_if_format_type_is_not_valid(format)

        try:
            df_sales = self.spark.read.format(format)\
                .load(self.config["databricks"]["data"]["input_file_sales"])
            df_art_german_names = self.spark.read.format(format)\
                .load(self.config["databricks"]["data"]["input_file_german_art_names"])\
                .select(*column_to_select_from_ds_with_german_art_names.values())
            df_art_bg_names = self.spark.read.format(format)\
                .load(self.config["databricks"]["data"]["input_file_articles_with_bg_names"])
        except ValueError as error:
            logger.error("Invalid path to dataset!")
            raise ValueError("Invalid path to dataset!", str(error))

        logger.info('Successfully open the input files')
        return df_sales, df_art_german_names, df_art_bg_names

    def _transform(self, read_dfs):
        df_sales, df_art_german_names, df_art_bg_names = read_dfs

        logger.info("Doing transformation...")

        logger.info("Filtering df by the last 5 weeks and extract only needed columns from here!")

        df_sales_for_period = get_needed_data_for_curr_period(df=df_sales,
                                                              date_column=start_date_col,
                                                              period_in_weeks=period_in_weeks)

        df_sales_for_last_5_weeks = select_columns(df_sales_for_period,
                                                   *useful_columns_from_sales_df.values())

        logger.info('Successfully filter df by the last 5 weeks!')

        logger.info('Detect inconsistencies in the data: missing bon rows. '
                    'Filtering only correct bon ids and then create new df with joining without removing the duplicates'
                    'for each id because the kl_art_id is different.')

        correct_bon_ids_df = get_correct_bon_id(df=df_sales_for_last_5_weeks,
                                                column=useful_columns_from_sales_df["bons_column"])
        logger.info("Successfully collect only correct bon id's!")

        correctDF = drop_columns(joining_df(df1=df_sales_for_last_5_weeks,
                                            df2=correct_bon_ids_df,
                                            column=useful_columns_from_sales_df["bons_column"],
                                            way_to_join="leftsemi"),
                                 [useful_columns_from_sales_df["bons_column"],
                                  useful_columns_from_sales_df["bon_line_col"]])

        logger.info("Successfully create new DF with joined information from two df's with only correct bon id's")

        logger.info("Load datasets with bg names and german names and merge them into one dataframe so "
                    "can have item descriptions in both languages for better illustration.")

        logger.info("Filter dataset with bg_names by spr_id = 18")
        # because spr_id = 22 is for german names

        df_articles_names_bg = select_columns(filter_data(df=df_art_bg_names,
                                                          column=column_to_select_from_ds_with_bg_art_names["id_for_bg_names"],
                                                          filter_by="18"),
                                              column_to_select_from_ds_with_bg_art_names["art_name_bg_col"],
                                              column_to_select_from_ds_with_bg_art_names["column_to_join_by"])

        df_with_art_names_bg_and_german = joining_df(df1=df_art_german_names,
                                                     df2=df_articles_names_bg,
                                                     column=column_to_select_from_ds_with_bg_art_names["column_to_join_by"],
                                                     way_to_join="inner")\
            .drop(column_to_select_from_ds_with_bg_art_names["column_to_join_by"])

        logger.info("Merge dataframes into one common dataframe with the correct bond_ids and item names "
                    "in bg and german.")

        filtered_df_sales = joining_df(df1=correctDF,
                                       df2=df_with_art_names_bg_and_german,
                                       column=useful_columns_from_sales_df["article_id"],
                                       way_to_join="inner")

        logger.info("Successfully did the transformations!")

        return filtered_df_sales

    def _load(self, result_dfs):
        filtered_df_sales = result_dfs

        logger.info("Writing data back to storage account...")

        try:
            path_to_save = self.config["databricks"]["data"]["output_file_with_filtered_sales_ds"]
            (filtered_df_sales
             .write.mode("overwrite")
             .option("header", True)
             .format(format)
             .save(f"{path_to_save}"))
            logger.info("Saved output successfully.")
        except ValueError as error:
            logger.error(error)
            raise ValueError("Save Failed!")