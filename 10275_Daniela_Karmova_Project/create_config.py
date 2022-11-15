"""
Extends common config by stage-specific config and generates consolidated config file.

The script extends the common HOCON config (COMMON.conf) by the stage specific config according to the
stage parameter given and then creates a consolidated config of the given format (YAML, JSON or HOCON). The consolidated
config is then written to the output path given. The input directory for the config files can be specified optionally.
"""

import argparse
import logging
from argparse import ArgumentDefaultsHelpFormatter
from pathlib import Path
from typing import Optional

from pyhocon import ConfigFactory, ConfigTree, HOCONConverter
from pyhocon.config_parser import ConfigParser

logger = logging.getLogger("create_config")


class NoCommonConfigFoundException(Exception):
    pass


def create_config(conf_path: str, stage: Optional[str] = None) -> ConfigTree:
    """Merge a cross-stage HOCON config file (COMMON.conf) with an optional stage-specific config file.

    Args:
        conf_path: Input directory for all config files
        stage: Stage for which to look for a stage-specific config file

    Returns:
        Merged PyHOCON config tree
    """
    common_config_file = Path(f"{conf_path}/COMMON.conf")

    if not common_config_file.exists():
        logger.error("No COMMON config found.")
        raise NoCommonConfigFoundException

    config = ConfigFactory.parse_file(common_config_file, resolve=False)

    if stage:
        logger.info(f"Deployment stage: {stage}")
        stage_config_file = Path(f"{conf_path}/{stage}.conf")

        if stage_config_file.exists():
            logger.info(f"Use COMMON config and merge {stage} config.")
            stage_config = ConfigFactory.parse_file(stage_config_file, resolve=False)
            config = ConfigTree.merge_configs(config, stage_config)
        else:
            logger.info(f"No stage-specific config found for {stage}, use COMMON config.")
    else:
        logger.info("Deployment stage parameter not set, use COMMON config.")

    ConfigParser.resolve_substitutions(config)
    return config


def export_config(config: ConfigTree, output_file: str, output_format: str) -> None:
    """Export a given PyHOCON config to a file in the given format.

    Args:
        config: PyHOCON config tree
        output_file: Output file path
        output_format: Output format (yaml, json or hocon)

    Returns:
        None

    """
    config_str = HOCONConverter.convert(config, output_format)
    # https://bugs.python.org/issue23706 write_text should include a newline argument, fixed in Python 3.10
    # A line needs to have a terminating <newline> character according to POSIX specs:
    # https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap03.html#tag_03_206
    # Without that terminating <newline> character a line is not a line and will not be visible in the
    # Azure DevOps console log output.
    # write_text uses open with mode 'w', which may convert '\n' characters to a platform-specific representation
    Path(output_file).write_text(config_str + '\n')


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Generate consolidated configuration file from common and (optionally) stage-specific HOCON "
                    "config files. A COMMON.conf file must be located in the input directory.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("output", type=str, metavar="OUTPUT_FILE", help="The output file name")
    parser.add_argument(
        "-i", "--input", type=str, default="conf", help="The input directory containing the config files."
    )
    parser.add_argument(
        "-s", "--stage", type=str, help="The stage for which a stage-specific config should be merged (e.g. DEV)."
    )
    parser.add_argument(
        "-f", "--format", type=str, default="yaml", choices=["yaml", "json", "hocon"], help="The output format."
    )
    args = parser.parse_args()

    try:
        config_merged = create_config(args.input, args.stage)
        export_config(config_merged, args.output, args.format)
    except NoCommonConfigFoundException:
        exit(1)
