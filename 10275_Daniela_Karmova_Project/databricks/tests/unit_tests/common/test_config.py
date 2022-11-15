import unittest
from pathlib import Path

from uapc_tpl.common.config import create_config

TESTS_RESOURCES_ROOT_PATH = Path(__file__).parents[2] / 'resources'


class ConfigTestCase(unittest.TestCase):
    def test_create_config(self):
        conf_path = str(TESTS_RESOURCES_ROOT_PATH / 'test_conf.json')
        config = create_config(conf_path=conf_path)

        self.assertEqual(config["data"]["input_file"], "some/input/file")
        self.assertEqual(config["data"]["output_file"], "some/output/file")
        self.assertEqual(config["project"]["id"], "some_id")


if __name__ == '__main__':
    unittest.main()
