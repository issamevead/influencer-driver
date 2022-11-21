from __future__ import annotations

import ast
from contextlib import suppress
import datetime
import json
from random import randint
import sched
import time
from pathlib import Path

from dotenv import load_dotenv

from log.logger import Logs
from models.facebook import Facebook
from models.instagram import Instagram
from utils.util import get_env, sleeptime, time_bound, to_seconds
from connectors.mongo_db import TextMongoDatabase

load_dotenv()

NEXT_UPDATE = ast.literal_eval(get_env("NEXT_UPDATE"))
MX, MN = 23, 7
WAIT_NIGHT = 4

db = TextMongoDatabase("cookies")
s = sched.scheduler(time.time, time.sleep)
logs = Logs()


def get_profiles(social_media: str) -> list:
    """Get the profiles from the database"""
    try:
        with Path(get_env("PROFILES_CREDTS")).open(encoding="UTF-8") as source:
            return json.load(source)[social_media]
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logs.error(e)
        return []


def needed_time():
    """Get the time to wait until the next update"""
    next_update = to_seconds(NEXT_UPDATE)
    if time_bound(MX, MN):
        next_update = to_seconds(int(WAIT_NIGHT + NEXT_UPDATE))
    return next_update


def get_item(data: list, user: str) -> dict:
    """Get the item from the database"""
    for e in data:
        if e.get("profile_id") == user:
            return e.get("last_update")
    return None


def facebook_robot(profile: dict):
    """Run the Facebook robot"""
    facebook = Facebook(**profile)
    facebook.run()
    next_run = needed_time()
    logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
    s.enter(next_run, 1, facebook_robot, argument=(profile,))


def instagram_robot(profile: dict):
    """Run the Instagram robot"""
    instagram = Instagram(**profile)
    instagram.run()
    next_run = needed_time()
    logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
    s.enter(next_run, 1, instagram_robot, argument=(profile,))


if __name__ == "__main__":
    data = db.read_all({})
    profiles_facebook = get_profiles("facebook")
    profiles_instagram = get_profiles("instagram")

    for profile in profiles_facebook:
        last_update = get_item(data, profile.get("username"))
        if last_update:
            now = datetime.datetime.now()
            wait = now - datetime.datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
            if wait.total_seconds() < needed_time():
                logs.info(
                    f"Facebook | {profile.get('username')} will be updated in {round(wait.total_seconds()/3600,2)} Hour(s)"
                )
                s.enter(wait.total_seconds(), 1, facebook_robot, argument=(profile,))
        else:
            logs.info(
                f"Facebook | {profile.get('username')} will be updated in {round(wait.total_seconds()/3600,2)} Hour(s)"
            )
            s.enter(randint(60, 120), 1, facebook_robot, argument=(profile,))

    for profile in profiles_instagram:
        last_update = get_item(data, profile.get("username"))
        if last_update:
            wait = datetime.datetime.now() - datetime.datetime.strptime(
                last_update, "%Y-%m-%d %H:%M:%S"
            )
            if wait.total_seconds() < needed_time():
                logs.info(
                    f"Instagram | {profile.get('username')} will be updated in {round(wait.total_seconds()/3600,2)} Hour(s)"
                )
                s.enter(wait.total_seconds(), 1, instagram_robot, argument=(profile,))
        else:
            logs.info(
                f"Instagram | {profile.get('username')} will be updated in {round(wait.total_seconds()/3600,2)} Hour(s)"
            )
            s.enter(randint(60, 120), 1, instagram_robot, argument=(profile,))

    s.run()
