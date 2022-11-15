import logging
from uapc_aiacad.common.abstract_vis import AbstractEvlVis
from uapc_aiacad.visualization.visualization_transformation import *
from uapc_aiacad.transformations.get_most_purchased_and_less_purchased_articles_per_unit_of_measure import *
from uapc_aiacad.common.validation import Validator

logger = logging.getLogger(__name__)

loading_data_format = "delta"


class VisTopAndFlopArtPerWeightEvlVis(AbstractEvlVis):

    def run(self):
        df = self._extract()
        result_dfs = self._visualise(df)
        self._load(result_dfs)

    def _extract(self):
        logger.info("Starting VisCustomersForHours")
        logger.info("input_file_top10_per_kg  = %s", self.config["databricks"]["data"]["output_file_top10_per_kg"])
        logger.info("input_file_less10_per_kg  = %s", self.config["databricks"]["data"]["output_file_less10_per_kg"])
        logger.info("output_file  = %s", self.config["databricks"]["data"]["vis_top_10_per_weight_file"])
        logger.info("output_file  = %s", self.config["databricks"]["data"]["vis_less_10_per_weight_file"])

        Validator.raise_if_format_type_is_not_valid(loading_data_format)

        try:
            df_top10_per_weight = self.spark.read.format(loading_data_format).load(
                self.config["databricks"]["data"]["output_file_top10_per_kg"])
            df_less10_per_weight = self.spark.read.format(loading_data_format).load(
                self.config["databricks"]["data"]["output_file_less10_per_kg"])
        except ValueError as error:
            logger.error("Invalid path to dataset!")
            raise ValueError("Invalid path to dataset!", str(error))
        # I do not make vis for df with 10 of the least purchased art per unit, because all articles
        # there are with quantity 1.0
        logger.info('Successfully open the input files')
        return df_top10_per_weight, df_less10_per_weight

    def _visualise(self, df):
        df_top10_per_weight, df_less10_per_weight = df

        logger.info("Doing visualisation...")

        logger.info("Visualize df with top 10 articles sold per weight")
        print("----------------------------------------------------------------------------------")
        print("ACTUAL VISUALIZED DF WITH TOP 10 ARTICLES SOLD PER WEIGHT")

        vis_of_df_top10_per_weight = creating_visualization_from_df(df=df_top10_per_weight,
                                                                    x_axis_col="quantity_per_weight_kg",
                                                                    y_axis_col="names_of_articles_gm",
                                                                    unit_of_measure="weight in kg",
                                                                    top="most"
                                                                    )

        logger.info("Visualize df with less 10 articles sold per weight")
        print("----------------------------------------------------------------------------------")
        print("ACTUAL VISUALIZED DF WITH 10 LEAST PURCHASED ARTICLES SOLD PER WEIGHT")
        vis_of_df_less10_per_weight = creating_visualization_from_df(df=df_less10_per_weight,
                                                                     x_axis_col="quantity_per_weight_kg",
                                                                     y_axis_col="names_of_articles_gm",
                                                                     unit_of_measure="weight in kg",
                                                                     top="least"
                                                                     )

        logger.info('Successfully did the visualization!')

        return vis_of_df_top10_per_weight, vis_of_df_less10_per_weight

    def _load(self, result_df_vis):
        vis_of_df_top10_per_weight, vis_of_df_less10_per_weight = result_df_vis

        logger.info("Writing the vis file to storage...")
        vis_of_df_top10_per_weight.savefig(self.config["databricks"]["data"]["vis_top_10_per_weight_file"])
        vis_of_df_less10_per_weight.savefig(self.config["databricks"]["data"]["vis_less_10_per_weight_file"])
        logger.info("Saved output successfully.")