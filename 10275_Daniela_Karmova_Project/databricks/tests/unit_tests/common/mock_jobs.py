"""Job Implementation for testing purposes"""
from uapc_tpl.common.abstract_job import AbstractEtlJob, AbstractJob
from typing import Dict, Any

class MockJobImplementation(AbstractJob):
    """Direct implementation of Abstract Job for testing

    Args:
        conf: str, path to config file
        test_arg: any, some argument for testing

    """

    def __init__(self, config: Dict[str, Any], test_arg):
        super().__init__(config)
        self.test_arg = test_arg

    def run(self):
        pass


class MockEtlJobImplementation(AbstractEtlJob):
    """Implementation of AbstractEtlJob for testing"""

    def __init__(self, config: Dict[str, Any], test_arg):
        super().__init__(config)
        self.test_arg = test_arg
        self.res_arg = None

    def _extract(self):
        return self.test_arg

    def _transform(self, read_dfs):
        test_arg = read_dfs
        return test_arg

    def _load(self, result_dfs):
        test_arg = result_dfs
        self.res_arg = test_arg


class MockJobStruct(AbstractJob):
    """Another AbstractJob implementation for testing the JobFactory with three different jobs"""

    def run(self):
        pass
