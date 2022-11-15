import logging
from uapc_aiacad.common.abstract_vis import AbstractEvlVis
from uapc_aiacad.visualization.visualization_transformation import *
from uapc_aiacad.transformations.get_most_purchased_and_less_purchased_articles_per_unit_of_measure import *
from uapc_aiacad.common.validation import Validator

logger = logging.getLogger(__name__)

loading_data_format = "delta"


class VisTopAndFlopArtPerUnitEvlJob(AbstractEvlVis):

    def run(self):
        df = self._extract()
        result_dfs = self._visualise(df)
        self._load(result_dfs)

    def _extract(self):
        logger.info("Starting VisCustomersForHours")
        logger.info("input_file_top10_per_unit  = %s", self.config["databricks"]["data"]["output_file_top10_per_unit"])
        logger.info("input_file_less10_per_unit  = %s", self.config["databricks"]["data"]["output_file_less10_per_unit"])
        logger.info("output_file  = %s", self.config["databricks"]["data"]["vis_top_10_per_unit_file"])

        Validator.raise_if_format_type_is_not_valid(loading_data_format)

        try:
            df_top10_per_unit = self.spark.read.format(loading_data_format).load(
                self.config["databricks"]["data"]["output_file_top10_per_unit"])
            df_10_of_the_least_purchased_per_unit = self.spark.read.format(loading_data_format).load(
                self.config["databricks"]["data"]["output_file_less10_per_unit"])
        except ValueError as error:
            logger.error("Invalid path to dataset!")
            raise ValueError("Invalid path to dataset!", str(error))
        # I do not make vis for df with 10 of the least purchased art per unit, because all articles
        # there are with quantity 1.0
        logger.info('Successfully open the input files')
        return df_top10_per_unit, df_10_of_the_least_purchased_per_unit

    def _visualise(self, df):
        df_top10_per_unit, df_10_of_the_least_purchased_per_unit = df

        logger.info("Doing visualisation...")

        logger.info("Visualize df with top 10 articles sold per unit")
        print("----------------------------------------------------------------------------------")
        print("ACTUAL VISUALIZED DF WITH TOP 10 ARTICLES SOLD PER UNIT")
        vis_of_df_top10_per_unit = creating_visualization_from_df(df=df_top10_per_unit,
                                                                  x_axis_col="quantity_per_unit",
                                                                  y_axis_col="names_of_articles_gm",
                                                                  unit_of_measure="unit",
                                                                  top="most")

        logger.info("Displaying without visualize because all 10 articles are with quantity 1.0")

        print("-----------------------------------------------------------------------")
        print("DataFrame with 10 of the least purchased articles per unit.")
        display_df(df_10_of_the_least_purchased_per_unit)
        print("-----------------------------------------------------------------------")

        logger.info('Successfully did the visualization!')

        return vis_of_df_top10_per_unit

    def _load(self, result_df_vis):
        vis_of_df_top10_per_unit = result_df_vis

        logger.info("Writing the vis file to storage...")
        vis_of_df_top10_per_unit.savefig(self.config["databricks"]["data"]["vis_top_10_per_unit_file"])

        logger.info("Saved output successfully.")