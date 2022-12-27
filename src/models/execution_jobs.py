from __future__ import annotations

import ast
import asyncio
import datetime
import sched
import time
from collections import deque
from contextlib import suppress
from threading import Thread
from typing import Optional

import requests

from connectors.mongo_db import TextMongoDatabase
from dotenv import load_dotenv
from log.logger import Color, Logs
from utils.util import get_env, get_item, get_profiles, time_bound, to_seconds
from models.facebook import Facebook
from models.instagram import Instagram
from mitmp import run_mitm

load_dotenv()

NEXT_UPDATE = ast.literal_eval(get_env("NEXT_UPDATE"))
PROFILES_CREDTS = get_env("PROFILES_CREDTS")
DATABASE_COLLECTION_NAME = get_env("DATABASE_COLLECTION_NAME")
WAIT_NIGHT = 4


logs = Logs()


class ExecutionJob:

    data: Optional[list]
    profiles_facebook: Optional[list]
    profiles_instagram: Optional[list]
    date_format: str = "%Y-%m-%d %H:%M:%S"
    db = TextMongoDatabase(DATABASE_COLLECTION_NAME)
    s = sched.scheduler(time.time, time.sleep)

    def __init__(self, profiles_path: str, dq: deque) -> None:
        self.data = self.db.read_all({})
        self.profiles_facebook = get_profiles("facebook", profiles_path)
        self.profiles_instagram = get_profiles("instagram", profiles_path)
        self.dq = dq

    def mitm_proxy_status(self):
        for _ in range(3):
            with suppress(requests.exceptions.RequestException):
                r = requests.get("http://mitm.it/", timeout=5)
                if r.status_code == 200:
                    return
        raise ValueError("mitmproxy is not working")

    def start_thread(self):
        mm_proxy = Thread(target=run_mitm, args=(self.dq,))
        mm_proxy.daemon = True
        mm_proxy.start()
        time.sleep(20)

    def is_it_time(self, existing_date: str, hourly_nights: list = [23, 7]):
        now_ = datetime.datetime.now()
        if not (now_.hour < hourly_nights[0] and now_.hour > hourly_nights[1]):
            return False
        save_time = datetime.datetime.strptime(existing_date, "%Y-%m-%d %H:%M:%S")
        if (now_ - save_time).seconds < 2 * 3600:
            return False
        return True

    def facebook_robot(self, username, password):
        """Run the Facebook robot"""

        logs.info(f"Processing for {username} | Begin")
        self.dq.clear()
        unblocked_profile = self.db.read_all({"profile_id": username})
        saved_at = unblocked_profile[0].get("last_update", None)
        if self.is_it_time(saved_at):
            self.start_thread()
            with suppress(AttributeError, IndexError):
                if unblocked_profile and unblocked_profile[0].get("status") != 1:
                    logs.info(
                        f"{username} {Color.RED.format('Blocked')}, try to unlock it"
                    )
                    return
                args = {
                    "username": username,
                    "password": password,
                    "proxy": None,
                    "dq": self.dq,
                }
                self.mitm_proxy_status()
                facebook = Facebook(**args)
                facebook.run()
                logs.info(f"Processing for {username} | END")
        logs.info(f"Cookies for {username} still fresh")

    def instagram_robot(self, username, password):
        """Run the Instagram robot"""

        logs.info(f"\nProcessing for {username}| Begin")
        self.dq.clear()
        unblocked_profile = self.db.read_all({"profile_id": username})
        saved_at = unblocked_profile[0].get("last_update", None)
        if self.is_it_time(saved_at):
            self.start_thread()
            with suppress(AttributeError, IndexError):
                if unblocked_profile and unblocked_profile[0].get("status") != 1:
                    logs.info(
                        f"{username} {Color.RED.format('Blocked')}, try to unlock it"
                    )
                    return
                args = {
                    "username": username,
                    "password": password,
                    "proxy": None,
                    "dq": self.dq,
                }
                self.mitm_proxy_status()
                instagram = Instagram(**args)
                instagram.run()
                logs.info(f"Processing for {username} | END")
                return
        logs.info(f"Cookies for {username} still fresh")

    def run_jobs(self, args):
        network, username, password = args
        if network == "facebook":
            self.facebook_robot(username, password)
        if network == "instagram":
            self.instagram_robot(username, password)
