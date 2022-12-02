from __future__ import annotations

import ast
import datetime
import json
import os
import sched
import time
from collections import deque
from contextlib import suppress
from pathlib import Path
from threading import Thread
import asyncio

from dotenv import load_dotenv

from connectors.mongo_db import TextMongoDatabase
from log.logger import Color, Logs
from mitmp import run_mitm
from models.facebook import Facebook
from models.instagram import Instagram
from utils.util import get_env, time_bound, to_seconds

load_dotenv()

NEXT_UPDATE = ast.literal_eval(get_env("NEXT_UPDATE"))
MX, MN = 23, 7
WAIT_NIGHT = 4

dq = deque()
db = TextMongoDatabase("cookies")
s = sched.scheduler(time.time, time.sleep)
logs = Logs()

mitmproxy = Thread(name="mitmproxy server", target=run_mitm, args=(dq,))
mitmproxy.daemon = True


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


def facebook_robot(profile: dict, db: TextMongoDatabase, dq: deque):
    """Run the Facebook robot"""
    dq.clear()
    mitmproxy.start()
    unblocked_profile = db.read_all({"profile_id": profile.get("username")})
    with suppress(AttributeError, IndexError):
        if unblocked_profile and unblocked_profile[0].get("status") != 1:
            logs.info(
                f"{profile.get('username')} {Color.RED.format('Blocked')}], try to unlock it"
            )
            return
        args = {
            "username": profile.get("username"),
            "password": profile.get("password"),
            "proxy": profile.get("proxy"),
            "dq": dq,
        }
        facebook = Facebook(**args)
        facebook.run()
        next_run = needed_time()
        logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
        s.enter(next_run, 1, facebook_robot, argument=(profile, db))
    mitmproxy.join()


def instagram_robot(profile: dict, db: TextMongoDatabase, dq: deque):
    """Run the Instagram robot"""
    dq.clear()
    # asyncio.run(mitmproxy.start())
    mitmproxy.start()
    unblocked_profile = db.read_all({"profile_id": profile.get("username")})
    with suppress(AttributeError, IndexError):
        if unblocked_profile and unblocked_profile[0].get("status") != 1:
            logs.info(
                f"{profile.get('username')} {Color.RED.format('Blocked')}], try to unlock it"
            )
            return
        args = {
            "username": profile.get("username"),
            "password": profile.get("password"),
            "proxy": profile.get("proxy"),
            "dq": dq,
        }
        instagram = Instagram(**args)
        instagram.run()
        next_run = needed_time()
        logs.info(f"Next update will be in {next_run/3600} Hour(s)\n")
        s.enter(next_run, 1, instagram_robot, argument=(profile, db, dq))
    mitmproxy.join()


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
            s.enter(0, 1, facebook_robot, argument=(profile, db, dq))
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
            s.enter(next_run, 1, facebook_robot, argument=(profile, db, dq))
            continue
        logs.info(f"Facebook {profile.get('username')} updated in few seconds")
        s.enter(0, 1, facebook_robot, argument=(profile, db, dq))

    for profile in profiles_instagram:
        unblocked_profile = get_item(data, profile.get("username"))
        message = "Instagram | {} will be updated in {} Hour(s)"

        if unblocked_profile is None:
            logs.info(f"Facebook {profile.get('username')} updated in few seconds")
            s.enter(0, 1, instagram_robot, argument=(profile, db, dq))
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
            s.enter(next_run, 1, instagram_robot, argument=(profile, db, dq))
            continue
        logs.info(f"Instagram {profile.get('username')} updated in few seconds")
        s.enter(0, 1, instagram_robot, argument=(profile, db, dq))

    s.run()
