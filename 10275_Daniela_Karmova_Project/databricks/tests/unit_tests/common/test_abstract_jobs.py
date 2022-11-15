import unittest

from unit_tests.common.mock_jobs import MockEtlJobImplementation, MockJobImplementation


class TestAbstractJobs(unittest.TestCase):
    def setUp(self):
        self.config = {
            'storage': {
                'mount_point': 'some'
            },
            'data': {
                'input_file': 'some/input/file',
                'output_file': 'some/output/file'
            },
            'project': {
                'id': 'some_id'
            }
        }
        self.test_arg = "test_arg"

    def test_abstract_class(self):
        job = MockJobImplementation(self.config, self.test_arg)
        self.general_test(job, "MockJobImplementation")

    def test_etl_class(self):
        job = MockEtlJobImplementation(self.config, self.test_arg)
        self.general_test(job, "MockEtlJobImplementation")
        self.run_etl_test(job)

    def general_test(self, job, expected_name):
        self.app_name_test(job, expected_name)

    def run_etl_test(self, job):
        job.run()
        self.assertEqual(self.test_arg, job.res_arg)

    def app_name_test(self, job, expected_name):
        self.assertEqual(job.spark.conf.get("spark.app.name"), expected_name)
