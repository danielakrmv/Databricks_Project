"""Abstract Job classes. Jobs serve as a point of entry to the application. They set up a config and the SparkSession.
They are to be registered in the JobFactory so that they can be retrieved in the run_job notebook.
Using request_construct_args() the notebook can request the respective args via the JObFactory from airflow
(dbutils.widgets.get()).

"""
from abc import abstractmethod
from typing import Dict, Any

from pyspark.sql import SparkSession


class AbstractJob:
    """Abstract Job class - each Job must implement run

    Args:
        config: Python dictionary containing project configuration

    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.spark = SparkSession.builder.appName(self.__class__.__name__).getOrCreate()

    @abstractmethod
    def run(self):
        """Main method of class - runs the main workflow"""
        raise NotImplementedError


class AbstractEtlJob(AbstractJob):
    """Abstract Class for ETL jobs - must implement _extract, _transform and _load"""

    def run(self):
        read_dfs = self._extract()
        result_dfs = self._transform(read_dfs)
        self._load(result_dfs)

    @abstractmethod
    def _extract(self):
        """Extract Step - Load the data

        Returns:
            iterable[pyspark.DataFrame], all read dataframes

        """
        raise NotImplementedError

    @abstractmethod
    def _transform(self, read_dfs):
        """Transform Step - Transformation operations on the data. Potential input should be output of _extract

        Args:
            read_dfs: iterable[pyspark.DataFrame], all dataframes read in _extract.

        Returns:
            iterable[pyspark.DataFrame], all transformed dataframes to be written.

        """
        raise NotImplementedError

    @abstractmethod
    def _load(self, result_dfs):
        """Load Step - Writes the data. Potential input should be output of _transform

        Args:
            result_dfs: iterable[pyspark.DataFrame], all resulting dataframes to be written.

        Returns:
            None

        """
        raise NotImplementedError


class AbstractPredictJob(AbstractJob):
    """Abstract Class for Predict jobs - must implement _extract, _transform and _visualize_prediction_plot.
    Its usefully for the bonus task with linear regression"""

    def run(self):
        read_dfs = self._extract()
        result_to_vis_dfs = self._transform(read_dfs)
        self._visualize_prediction_plot(result_to_vis_dfs)

    @abstractmethod
    def _extract(self):
        """Extract Step - Load the data

        Returns:
            iterable[pyspark.DataFrame], all read dataframes

        """
        raise NotImplementedError

    @abstractmethod
    def _transform(self, read_dfs):
        """Transform Step - Transformation operations on the data.
        Potential input should be output of _extract 

        Args:
            read_dfs: iterable[pyspark.DataFrame], all dataframes read in _extract.

        Returns:
            iterable[pyspark.DataFrame]

        """
        raise NotImplementedError

    @abstractmethod
    def _visualize_prediction_plot(self, result_to_vis_dfs):
        """Visualize step - do prediction using linear regression and visualize it. 
        Potential input should be output of _transform

        Args:
            result_to_vis_dfs: iterable[pyspark.DataFrame], all resulting dataframes to be written.

        Returns:
            None

        """
        raise NotImplementedError
