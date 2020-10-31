"""
Some auxiliary entities not falling into other categories
"""

import collections
import configparser
import copy
import json
import subprocess
import sys
import time
from typing import Any, List, Mapping

import stm32pio.core.settings


def _get_version_from_scm() -> str:
    try:
        import setuptools_scm  # setuptools_scm is the dev-only dependency
    except ImportError:
        return 'Portable (not-installed). See git tag'
    else:
        # Calculate the version in real-time from the Git repo state
        return setuptools_scm.get_version(root='../..', relative_to=__file__)

def get_version() -> str:
    """Retrieve the app version as string"""
    if sys.version_info >= (3, 8):
        import importlib.metadata
        try:
            # For modern Python use the package metadata (if we are installed). For this to be available the wheel build
            # should be done with setuptools_scm
            return importlib.metadata.version('stm32pio')
        except importlib.metadata.PackageNotFoundError:
            # stm32pio is not installed (i.e. running from sources)
            return _get_version_from_scm()
    else:
        try:
            # Version is stored in the stm32pio/core/version.py file auto-generated by setuptools_scm tool
            import stm32pio.core.version
        except ImportError:
            # Version file is not available, most likely we are not installed (i.e. running from sources)
            return _get_version_from_scm()
        else:
            return stm32pio.core.version.version


_pio_boards_cache: List[str] = []
_pio_boards_cache_lifetime: float = 5.0
_pio_boards_fetched_at: float = 0

def get_platformio_boards() -> List[str]:
    """
    Obtain the PlatformIO boards list. As we interested only in STM32 ones, cut off all of the others. Additionally,
    establish a short-time "cache" to prevent the overflooding with requests to subprocess.

    IMPORTANT NOTE: PlatformIO can go to the Internet from time to time when it decides that its cache is out of date.
    So it MAY take a long time to execute.
    """

    global _pio_boards_fetched_at, _pio_boards_cache, _pio_boards_cache_lifetime

    current_time = time.time()
    if len(_pio_boards_cache) == 0 or (current_time - _pio_boards_fetched_at > _pio_boards_cache_lifetime):
        # Windows 7, as usual, correctly works only with shell=True...
        result = subprocess.run(f"{stm32pio.core.settings.config_default['app']['platformio_cmd']} boards "
                                f"--json-output stm32cube", encoding='utf-8', shell=True, stdout=subprocess.PIPE,
                                check=True)
        _pio_boards_cache = [board['id'] for board in json.loads(result.stdout)]
        _pio_boards_fetched_at = current_time

    return copy.copy(_pio_boards_cache)


def cleanup_dict(mapping: Mapping[str, Any]) -> dict:
    """Recursively copy non-empty values to the new dictionary. Return this new dict"""
    cleaned = {}

    for key, value in mapping.items():
        if isinstance(value, collections.abc.Mapping):
            cleaned[key] = cleanup_dict(value)
        elif value is not None and value != '':
            cleaned[key] = value

    return cleaned


def configparser_to_dict(config: configparser.ConfigParser) -> dict:
    """Convert configparser.ConfigParser instance to a dictionary"""
    return {section: {key: value for key, value in config.items(section)} for section in config.sections()}


