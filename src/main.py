from __future__ import annotations

import ast
from contextlib import suppress
import json
import sched
import time
from pathlib import Path

from dotenv import load_dotenv

from log.logger import Logs
from models.facebook import Facebook
from models.instagram import Instagram
from utils.util import get_env, sleeptime, time_bound, to_seconds

load_dotenv()

NEXT_UPDATE = ast.literal_eval(get_env("NEXT_UPDATE"))
MX, MN = 23, 7
WAIT_NIGHT = 4

s = sched.scheduler(time.time, time.sleep)
logs = Logs()


def get_profiles(socila_media: str) -> list:
    """Get the profiles from the database"""
    try:
        with Path(get_env("PROFILES_CREDTS")).open(encoding="UTF-8") as source:
            return json.load(source)[socila_media]
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logs.error(e)
        return []


def needed_time():
    """Get the time to wait until the next update"""
    next_update = to_seconds(NEXT_UPDATE)
    if time_bound(MX, MN):
        next_update = to_seconds(int(WAIT_NIGHT + NEXT_UPDATE))
    return next_update


def facebook_robot():
    """Run the Facebook robot"""
    for profile in get_profiles("facebook"):
        facebook = Facebook(**profile)
        facebook.run()
        sleeptime()
    next_run = needed_time()
    logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
    s.enter(next_run, 1, facebook_robot)


def instagram_robot():
    """Run the Instagram robot"""
    for profile in get_profiles("instagram"):
        instagram = Instagram(**profile)
        instagram.run()
        sleeptime()
    next_run = needed_time()
    logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
    s.enter(next_run, 1, instagram_robot)


if __name__ == "__main__":
    s.enter(0, 1, facebook_robot)
    s.enter(0, 1, instagram_robot)
    s.run()
