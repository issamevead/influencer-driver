import datetime
import os
import signal
import time
from contextlib import suppress
from pathlib import Path
from random import randint
from typing import Any, List, Optional

from selenium.webdriver.remote.webelement import WebElement

from log.logger import Logs


def get_env(key: str) -> Optional[str]:
    """Get the value of an environment variable
    Args:
        key (str): Key of the environment variable
    Returns:
        Union[str, None]: Return the value of the environment
        variable if it exits, otherwise returns None
    """
    if key and isinstance(key, str):
        return os.getenv(key, None)
    return None


def time_bound(upper_bound: int, lower_bound: int) -> bool:
    """Check if current time is between two bounds
    Args:
        upper_bound (int): Upper bound
        lower_bound (int): Lower bound
    Returns:
        bool: True if current time is between the bounds, otherwise False
    """
    now = datetime.datetime.now()
    return now.hour >= upper_bound or now.hour <= lower_bound


def to_seconds(hours: int) -> int:
    """Convert hours to seconds
    Args:
        hours (int): Hours to convert
    Returns:
        int: Seconds
    """
    return hours * 60 * 60


def sleeptime(mn_time: int = 60, mx_time: int = 120) -> None:
    """Get the time to sleep"""
    break_time = randint(mn_time, mx_time)
    Logs().info(f"BreakTime | {break_time} seconds")
    time.sleep(break_time)


def human_writing(selector: WebElement, text):
    """Simulate human writing"""
    for x in text:
        selector.send_keys(x)
        time.sleep(randint(0, 1000) / 900)


def list_profile_folders(path: str) -> list:
    """List all subfolders in a folder
    Args:
        path (str): Path to the folder
    Returns:
        list: List of subfolders
    """
    return [x for x in list(Path(path).iterdir()) if x.is_dir()]


def get_profile_path(path, username):
    """from profile folders path get the profile path for the corresponding username
    Args:
        path (str): Path to the folder
        username (str): Username of the profile
    Returns:
        str: Path to the profile otherwise None
    """
    paths = list_profile_folders(path)
    for p in paths:
        if p.name == username:
            return p
    return None


def path_exist(path_: str) -> bool:
    """Check if a path exists
    Args:
        path (str): Path to check
    Returns:
        bool: True if the path exists, otherwise False
    """
    return Path(path_).exists()


def json_extract(obj, key) -> List[Any]:
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, val in obj.items():
                if isinstance(val, (list, dict)) and k != key:
                    extract(val, arr, key)
                elif k == key:
                    arr.append(val)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def kill_process(process: str):
    """Kill a process by name
    Args:
        process(str): the name of the process
        >>> kill_process("firefox")
    """
    # TODO: implement the bellow cmd rather than the current one.
    # "pgrep 'process_name' | xargs sudo kill"
    with suppress(PermissionError):
        for pid in os.popen("pgrep " + process).read().splitlines():
            os.kill(int(pid), signal.SIGTERM)