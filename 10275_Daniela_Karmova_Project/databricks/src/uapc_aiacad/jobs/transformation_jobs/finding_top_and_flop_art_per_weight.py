import logging
from uapc_aiacad.common.abstract_job import AbstractEtlJob
from uapc_aiacad.transformations.get_most_purchased_and_less_purchased_articles_per_unit_of_measure import *
from uapc_aiacad.common.validation import Validator

logger = logging.getLogger(__name__)
format = "delta"

unit_of_measure_col = "einh_id"
article_id = "kl_art_id"
menge_col = "menge"
start_date_col = "k_bon_dat"

new_names_per_weight = ["article_id", "quantity_per_weight_kg", "action_flag", "names_of_articles_gm",
                        "group_names", "names_of_articles_bg"]


class FindTopAndFlopTenArticlesPerWeightEtlJob(AbstractEtlJob):

    def _extract(self):
        logger.info("Starting finding articles")

        logger.info("output_file_with_df_with_correct_bon_ids_and_names_of_art = %s",
                    self.config["databricks"]["data"]["output_file_with_filtered_sales_ds"])
        logger.info("output_file_with_10_most_purchased_articles_per_weight = %s",
                    self.config["databricks"]["data"]["output_file_top10_per_kg"])
        logger.info("output_file_with_10_less_purchased_articles_per_weight = %s",
                    self.config["databricks"]["data"]["output_file_less10_per_kg"])

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

        logger.info("Doing transformation...")

        logger.info("Using the sales data for Bulgaria for the last 5 weeks, "
                    "to make separate comparisons for articles that are sold per weight")

        dataSalesPerWeight = get_data_per_unit_of_measure(df=filtered_df_sales,
                                                          column_to_filter=unit_of_measure_col,
                                                          column_to_group_by=article_id,
                                                          unit_of_measure="KG")

        final_df_sales_per_weight = (joining_df(df1=dataSalesPerWeight,
                                                df2=filtered_df_sales,
                                                column=article_id,
                                                way_to_join="inner")
                                     .dropDuplicates([article_id])
                                     .drop(menge_col, unit_of_measure_col, start_date_col))

        logger.info("Successfully get only those articles, which are sold per weight and joined this df "
                    "with filtered_sales one.")

        logger.info("Renaming column in final_df_sales_per_weight for better illustration.")

        rename_final_df_sales_per_weight = rename_column(df=final_df_sales_per_weight,
                                                         new_names=new_names_per_weight)

        logger.info("Sorting 'rename_final_df_sales_per_weight' in descending order so can find "
                    "ten most purchased articles per weight.")

        ten_most_purchased_articles_per_weight = sorting_data_desc(rename_final_df_sales_per_weight, 
                                                                   ["quantity_per_weight_kg"])

        logger.info("Sorting 'rename_final_df_sales_per_weight' in ascending order so can find "
                    "ten least purchased articles per weight.")

        ten_less_purchased_articles_per_weight = sorting_data_asc(rename_final_df_sales_per_weight,
                                                                    ["quantity_per_weight_kg"])

        logger.info("Successfully did the transformation!")

        return ten_most_purchased_articles_per_weight, ten_less_purchased_articles_per_weight

    def _load(self, result_dfs):
        ten_most_purchased_articles_per_weight, ten_less_purchased_articles_per_weight = result_dfs

        logger.info("Writing data back to storage account...")

        try:
            ten_most_purchased_articles_per_weight\
                .write.mode("overwrite")\
                .option("header", True)\
                .format(format)\
                .save(self.config["databricks"]["data"]["output_file_top10_per_kg"])
            logger.info("Saved output successfully.")
        except ValueError as error:
            logger.info(error)
            raise ValueError("Save Failed!")

        try:
            ten_less_purchased_articles_per_weight\
                .write.mode("overwrite")\
                .option("header", True)\
                .format("delta")\
                .save(self.config["databricks"]["data"]["output_file_less10_per_kg"])
            logger.info("Saved output successfully.")
        except ValueError as error:
            logger.info(error)
            raise ValueError("Save Failed!")
