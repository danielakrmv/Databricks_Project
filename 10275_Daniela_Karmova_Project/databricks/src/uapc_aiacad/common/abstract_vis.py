from abc import abstractmethod
from typing import Dict, Any

from pandas import DataFrame
from pyspark.sql import SparkSession


class AbstractVis:
    """Abstract Vis class - each vis must implement run

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


class AbstractEvlVis(AbstractVis):
    """Abstract Class for EVL vis - must implement _extract, _visualise and _load"""

    def run(self):
        df = self._extract()
        result_dfs = self._visualise(df)
        self._load(result_dfs)

    @abstractmethod
    def _extract(self):
        """Extract Step - Load the data

        Returns:
            iterable[pyspark.DataFrame], all read dataframes

        """
        raise NotImplementedError

    @abstractmethod
    def _visualise(self, read_dfs):
        """Transform Step - Transformation operations on the data. Potential input should be output of _extract

        Args:
            read_dfs: iterable[pyspark.DataFrame], all dataframes read in _visualise.

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