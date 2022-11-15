import json
from typing import Dict, Any


def create_config(conf_path: str) -> Dict[str, Any]:
    """Read json at conf_path to python dict"""
    with open(conf_path, "r") as fh:
        config_dict = json.load(fh)

    return config_dict
