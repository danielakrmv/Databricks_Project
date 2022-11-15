"""
This module defines a basic logging-setup for uapc-projects.
"""
import logging
import logging.config
import sys
import io
from typing import Dict, Any


class CustomLogging:
    """ Sets up custom logging configuration

    Args:
        logging_conf: Dict[str, Any]: The "logging" part of
            the project configuration as python dictionary
            E.g.: ```
            logging {
                level = INFO,
                ...
            }
            ````
    """

    def __init__(self, logging_conf: Dict[str, Any]) -> None:
        self._logging_conf = logging_conf
        self._stream = None

    @property
    def stream(self):
        """ _stream variable property """
        return self._stream

    @stream.setter
    def stream(self, value):
        self._stream = value

    def setup_logging_basic(self) -> None:
        """Set basic logging configuration.

        Configuration of the root logger (existing handlers attached to the root logger are
        removed and closed) to log any message to stdout. Since project logger is a child of
        root logger all messages send via that logger are also send to stdout.

        Python logging module organizes loggers in a hierarchy. All loggers are  descendants
        of the root logger. Each logger passes log messages on to its parent. Which means if
        you create module level loggers using the logging.getLogger("__name__") approach they
        are configured to send logs (depending on the logging_conf) to the Log Analytics Workspace.

        Args:

        Returns:
            None
        """
        # Set stream variable
        self._stream = io.StringIO()

        # Log everything to a stream variable
        logging.basicConfig(
            level=self._logging_conf['level'],
            stream=self._stream,
            format=self._logging_conf['format']
        )

        # Set formatter
        formatter = logging.Formatter(self._logging_conf['format'])

        # Set Additional Handlers
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel('ERROR')
        ch.setFormatter(formatter)

        # Add handlers
        logging.getLogger('').addHandler(ch)

        # Configure project logger:
        # 1. Since it's a child of the root logger,
        # everything that is logged via the project logger is also put to stdout
        # 2. Assuming __name__ is used for module level logger names
        project_logger_name = __name__.split('.')[0]
        project_logger = logging.getLogger(project_logger_name)
        project_logger.setLevel(self._logging_conf['level'])

        # Raise log-level for py4j/spark logger
        spark_logger = logging.getLogger('py4j.java_gateway')
        spark_logger.setLevel(logging.ERROR)
        project_logger.info("Basic Logging Steup initialized!")

    def get_logs(self, log_path: str, dbutils):
        """
        Saves the log stream to file

        Args:
            log_path: str: path of log file
            dbutils: Databricks Utilities object

        Returns:
            None
        """
        dbutils.fs.put(log_path, self._stream.getvalue(), overwrite=True)

    def close_stream(self):
        """ Closes the log stream

        Returns:
            None
        """
        self._stream.close()

    @staticmethod
    def log_uncaught_exception(exception: Exception) -> None:
        """Log exception over the logging system. Exception information such as the traceback
        is added to the error log.

        Args:
            exception: The uncaught exception object

        Returns:
            None
        """
        # Assuming __name__ is used for module level logger names
        project_logger_name = __name__.split('.')[0]
        logger = logging.getLogger(project_logger_name)

        logger.critical(f'An uncaught exception happened: {exception}', exc_info=exception)
