import io
import json
import logging
import unittest
import datetime
from typing import Dict, Tuple
from unittest.mock import patch
from unittest import expectedFailure

from logstash_formatter import LogstashFormatterV1
from uapc_tpl.common.custom_json_encoder import JSONEncoderHandlingNaN

import numpy as np

from uapc_tpl.common import custom_logging, law_handler
from uapc_tpl.common.data_collector_api_client import DataCollectorAPIClient

_CUSTOM_LOG_TYPE = "TplCustomLogs"
_LOG_ANALYTICS_WORKSPACE_ID = "example_log_analytics_workspace_id"
_SHARED_KEY = "shared_key_example"


class DataCollectorApiClientMock(DataCollectorAPIClient):
    """Mock to simulate sending logs to log analytics api"""

    def __init__(self):
        self.events = []

    def post_data(self, log_type, json_records, record_timestamp=''):
        self.events.append({'event': json.loads(json_records), 'custom_log_type': log_type, 'timestamp': record_timestamp})


class CustomLoggingTestCase(unittest.TestCase):
    # assuming __name__ is used for module level logger names
    PROJECT_LOGGER_NAME = law_handler.__name__.split('.')[0]

    @staticmethod
    def _setup_logging_emit_logs_for_all_levels_using_project_logger(
            logging_config: Dict, shared_key: str = None
    ) -> Tuple[io.StringIO, DataCollectorApiClientMock]:

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
                patch.object(custom_logging, 'DataCollectorAPIClient') as create_mock_data_collector_api_client:
            mock_data_collector_api_client = DataCollectorApiClientMock()
            create_mock_data_collector_api_client.return_value = mock_data_collector_api_client

            custom_logging.setup_logging(logging_config, shared_key)
            project_logger = logging.getLogger(name=CustomLoggingTestCase.PROJECT_LOGGER_NAME)

            for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
                project_logger.log(level=logging.getLevelName(level), msg=f'test msg - {level}')

        return mock_stdout, mock_data_collector_api_client

    def setUp(self) -> None:
        # since we configure the root logger in each test we have to make sure to "reset" the logging system
        # otherwise we get unwanted test results
        for h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
            h.close()

    def test_custom_logging_with_law(self):
        """Test if a "law" key in conf enables law logging (add law handler to project logger)"""
        logging_config = {
            'law': {
                'log_analytics_workspace_id': 'some_log_analytics_workspace_id',
                'custom_log_type': 'TplCustomLogs'
            },
            'level': 'INFO'
        }

        # configure logging and create one log message for all python logging log levels
        mock_stdout, mock_data_collector_api_client = \
            self._setup_logging_emit_logs_for_all_levels_using_project_logger(logging_config, _SHARED_KEY)

        stream_handler_output = mock_stdout.getvalue().splitlines()
        law_handler_output = mock_data_collector_api_client.events

        # logging is configured with a stream and a log analytics handler set to level INFO
        # => 'logging initialized' message from setup_logging method + 1 messages per level higher than DEBUG
        self.assertEqual(len(stream_handler_output), 5)
        self.assertEqual(len(law_handler_output), 5)

    def test_custom_logging_without_law(self):
        """Test if a missing "law" key in conf disables law logging (add no law handler to project logger)"""
        logging_config = {'level': 'INFO'}

        # configure logging and create one log message for all python logging log levels
        mock_stdout, _ = self._setup_logging_emit_logs_for_all_levels_using_project_logger(logging_config)

        stream_handler_output = mock_stdout.getvalue().splitlines()
        # logging is configured with only a stream handler set to level INFO
        # => 'logging initialized' message from setup_logging method + 1 messages per level higher than DEBUG
        self.assertEqual(len(stream_handler_output), 5)

    def test_custom_logging_without_law_critical_log_level(self):
        """Test if different log levels work"""
        logging_config = {'level': 'CRITICAL'}

        # configure logging and create one log message for all python logging log levels
        mock_stdout, _ = self._setup_logging_emit_logs_for_all_levels_using_project_logger(logging_config)

        stream_handler_output = mock_stdout.getvalue().splitlines()
        # logging is configured with only a stream handler set to level CRITICAL
        # => 'logging initialized' message from setup_logging method + 1 messages per level higher than ERROR
        self.assertEqual(len(stream_handler_output), 1)


class LawHandlerTestCase(unittest.TestCase):

    def test_emit_should_format_log_message_as_valid_json(self):
        """Test to make sure that the message that was sent was formatted correctly."""
        data_collector_api_client_mock = DataCollectorApiClientMock()
        test_law_handler = law_handler.LawHandler(custom_log_type=_CUSTOM_LOG_TYPE,
                                                  data_collector_api_client=data_collector_api_client_mock)
        log_record = logging.makeLogRecord({'name': 'test', 'msg': np.inf})
        test_law_handler.emit(log_record)

        self.assertEqual(len(data_collector_api_client_mock.events), 1, 'More then 1 event send!')
        event = data_collector_api_client_mock.events[0]['event']
        self.assertEqual('inf', event['message'])
        self.assertEqual('test', event['name'])


# Mocking the requests.post method to test the data collector api client
def mocked_requests_post(uri, data, headers):
    return {'uri': uri, 'data': data, 'headers': headers}


@patch('requests.post', side_effect=mocked_requests_post)
class DataCollectorApiClientTestCase(unittest.TestCase):
    client = None
    formatter = None
    common_log_record = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = DataCollectorAPIClient(log_analytics_workspace_id=_LOG_ANALYTICS_WORKSPACE_ID, shared_key=_SHARED_KEY)
        cls.formatter = LogstashFormatterV1(json_cls=JSONEncoderHandlingNaN)
        cls.common_log_record = logging.makeLogRecord({'name': 'test', 'msg': np.inf})

    def test_post_data_should_return_valid_data(self, mock_post):

        iso_timestamp = datetime.datetime.now().isoformat()
        record_json = json.loads(self.formatter.format(self.common_log_record))

        response = self.client.post_data(_CUSTOM_LOG_TYPE, record_json, iso_timestamp)
        response_data = response['data']

        self.assertEqual(response['headers']['Log-Type'], _CUSTOM_LOG_TYPE)
        self.assertEqual(response_data['message'], 'inf')
        self.assertEqual(response_data['name'], 'test')
        self.assertEqual(response['headers']['time-generated-field'], iso_timestamp)
        self.assertTrue(str.startswith(response['headers']['Authorization'], f'SharedKey {_LOG_ANALYTICS_WORKSPACE_ID}:'))

    @expectedFailure
    def test_post_data_should_fail_for_invalid_log_type_due_to_invalid_symbols(self, mock_post):

        iso_timestamp = datetime.datetime.now().isoformat()
        record_json = self.formatter.format(self.common_log_record)

        self.client.post_data("Wrong-_&*Log_Type", record_json, iso_timestamp)

    @expectedFailure
    def test_post_data_should_fail_for_invalid_log_type_due_to_invalid_length(self, mock_post):
        iso_timestamp = datetime.datetime.now().isoformat()
        record_json = self.formatter.format(self.common_log_record)
        log_type = 20*'very_' + 'long_log_type'

        self.client.post_data(log_type, record_json, iso_timestamp)


if __name__ == '__main__':
    unittest.main()
