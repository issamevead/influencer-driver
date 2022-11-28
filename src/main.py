from __future__ import annotations

import ast
import datetime
import json

import sched
import time
from pathlib import Path

from dotenv import load_dotenv

from log.logger import Logs, Color
from models.facebook import Facebook
from models.instagram import Instagram
from utils.util import get_env, time_bound, to_seconds
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
            return e
    return None


def facebook_robot(profile: dict, db: TextMongoDatabase):
    """Run the Facebook robot"""
    unblocked_profile = db.read_all({"profile_id": profile.get("username")})
    if unblocked_profile and unblocked_profile.get("status") != 1:
        logs.info(
            f"{profile.get('username')} {Color.RED.format('Blocked')}], try to unlock it"
        )
        return
    facebook = Facebook(**profile)
    facebook.run()
    next_run = needed_time()
    logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
    s.enter(next_run, 1, facebook_robot, argument=(profile, db))


def instagram_robot(profile: dict, db: TextMongoDatabase):
    """Run the Instagram robot"""
    unblocked_profile = db.read_all({"profile_id": profile.get("username")})
    if unblocked_profile and unblocked_profile.get("status") != 1:
        logs.info(
            f"{profile.get('username')} {Color.RED.format('Blocked')}], try to unlock it"
        )
        return
    instagram = Instagram(**profile)
    instagram.run()
    next_run = needed_time()
    logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
    s.enter(next_run, 1, instagram_robot, argument=(profile, db))


if __name__ == "__main__":
    data = db.read_all({})
    profiles_facebook = get_profiles("facebook")
    profiles_instagram = get_profiles("instagram")
    date_format = "%Y-%m-%d %H:%M:%S"

    for profile in profiles_facebook:
        unblocked_profile = get_item(data, profile.get("username"))
        message = "Facebook | {} will be updated in {} Hour(s)"

        if unblocked_profile is None:
            logs.info(f"Facebook {profile.get('username')} updated in few seconds")
            s.enter(0, 1, facebook_robot, argument=(profile, db))
            continue

        if unblocked_profile.get("status") != 1:
            continue

        now = datetime.datetime.now()
        last_update = datetime.datetime.strptime(
            unblocked_profile.get("last_update"), date_format
        )
        wait = (now - last_update).seconds
        idle_time = needed_time()
        next_run = idle_time - wait
        if next_run > 0:
            logs.info(
                message.format(profile.get("username"), round(next_run / 3600, 2))
            )
            s.enter(next_run, 1, facebook_robot, argument=(profile, db))
            continue
        logs.info(f"Facebook {profile.get('username')} updated in few seconds")
        s.enter(0, 1, facebook_robot, argument=(profile, db))

    for profile in profiles_instagram:
        unblocked_profile = get_item(data, profile.get("username"))
        message = "Instagram | {} will be updated in {} Hour(s)"

        if unblocked_profile is None:
            logs.info(f"Facebook {profile.get('username')} updated in few seconds")
            s.enter(0, 1, facebook_robot, argument=(profile, db))
            continue

        if unblocked_profile.get("status") != 1:
            continue

        now = datetime.datetime.now()
        last_update = datetime.datetime.strptime(
            unblocked_profile.get("last_update"), date_format
        )
        wait = (now - last_update).seconds
        idle_time = needed_time()
        next_run = idle_time - wait
        if next_run > 0:
            logs.info(
                message.format(profile.get("username"), round(next_run / 3600, 2))
            )
            s.enter(next_run, 1, instagram_robot, argument=(profile, db))
            continue
        logs.info(f"Instagram {profile.get('username')} updated in few seconds")
        s.enter(0, 1, instagram_robot, argument=(profile, db))

    s.run()
