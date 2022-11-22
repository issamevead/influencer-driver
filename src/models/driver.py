import os
import shutil
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import Optional

from connectors.mongo_db import TextMongoDatabase
from dotenv import load_dotenv
from log.logger import Color, Logs
from selenium.webdriver.common.proxy import Proxy
from seleniumwire import webdriver
from utils.enums import AppType, DeviceId, Status, ZoneId
from utils.util import get_env, kill_process, path_exist

load_dotenv()

FIREFOX_PATH = get_env("FIREFOX_PATH")
DRIVER_PATH = get_env("DRIVER_PATH")

cookieDB = TextMongoDatabase(get_env("DATABASE_COLLECTION_SOURCE"))
logs = Logs()


@dataclass
class RequestBase:
    request_id: int
    page_id: int
    cookies: str
    profile_id: int
    robot_id: int
    device_id: int
    number_of_executions: int
    last_used: datetime
    last_update: datetime
    zone_id: int
    app_type: int
    status: int


class Driver(ABC):
    profile_path: str
    proxy: str
    color: str
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/78.4"
    )
    browser = None

    def __init__(
        self,
        profile_path: Optional[str] = None,
        proxy: Optional[str] = None,
        color=Color.RED,
    ):
        self.profile_path = profile_path
        self.color = color
        self.proxy = proxy
        self.browser = self._connect()

    def _connect(self):
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")

        options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_argument("useAutomationExtension", False)
        # options.add_argument("excludeSwitches", ["enable-automation"])
        # options.add_argument("disable-infobars")
        options.set_preference("general.useragent.override", self.user_agent)
        options.set_preference("dom.webnotifications.serviceworker.enabled", False)
        options.set_preference("dom.webnotifications.enabled", False)
        # options.set_preference("marionette", False)
        # options.set_preference("useAutomationExtension", False)
        # options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("network.proxy.type", 1)
        options.set_preference(
            "profile.default_content_setting_values.notifications", 1
        )

        if self.proxy not in (None, ""):
            proxy_config = {
                "proxyType": "MANUAL",
                "socksVersion": 5,
                "socksProxy": self.proxy,
            }
            options.proxy = Proxy(proxy_config)
        config = {"options": options, "executable_path": DRIVER_PATH}

        if self.profile_path:
            config["firefox_profile"] = self.profile_path

        if "seleniumwire" in webdriver.Firefox.__module__:
            # auto_config set to False to force driver follow the Selenium constructor.
            config["seleniumwire_options"] = {"auto_config": True}
        return webdriver.Firefox(**config)

    def close(self):
        self.browser.close()

    def clean_tmp_and_logs(self):
        """Clean tmp files"""
        try:
            shutil.rmtree(Path(self.browser.caps.get("moz:profile")))
            driver_log = "geckodriver.log"
            if path_exist(driver_log):
                os.remove(driver_log)
        except FileNotFoundError as e:
            Logs().warn(f"{e.strerror} - {e.filename}")

    def kill_driver(self):
        self.browser.service.process.send_signal(15)

    def update_local_cookie(self):
        if not path_exist(self.profile_path):
            os.mkdir(self.profile_path)
        profile = Path(self.browser.caps.get("moz:profile"))
        cookie_file = profile / "cookies.sqlite"
        shutil.copy(cookie_file, Path(self.profile_path) / "cookies.sqlite")
        logs.info(
            f"{self.color.format(self.__class__.__name__)} | profile {Color.DARK_YELLOW.format(self.username)} locally updated"
        )

    def blocked_status(self, username: str):
        """Update status as blocked for a given username"""
        cookieDB.update({"profile_id": username}, {"status": Status.BLOCKED.value})

    def update_mg_cookie(self, username: str, page_id: int):
        """Update cookie in mongo database
        Args:
            username(str): A row identifier which is the username of a profile
            page_id(str): the social website type
        """
        headers, content = self.get_cookies()
        if (headers is None) or (content is None):
            return
        profile_exist = cookieDB.select_(
            {"$and": [{"profile_id": username}, {"page_id": page_id}]}
        )
        if profile_exist:
            cookieDB.update(
                {"profile_id": username},
                {
                    "headers": headers,
                    "content": content,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "number_of_executions": 0,
                },
            )
            logs.info(
                f"{self.color.format(self.__class__.__name__)} | profile {Color.DARK_YELLOW.format(username)} updated"
            )
            return
        cookieDB.insert_text(
            asdict(
                RequestBase(
                    request_id=md5(username.encode()).hexdigest(),
                    page_id=page_id,
                    cookies=cookies,
                    profile_id=username,
                    robot_id=None,
                    device_id=DeviceId.DESKTOP.value,
                    number_of_executions=0,
                    last_used=None,
                    last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    zone_id=ZoneId.STORY.value,
                    app_type=AppType.BROWSER.value,
                    status=Status.ACTIVE.value,
                )
            )
        )
        logs.info(
            f"{self.color.format(self.__class__.__name__)} | New profile {Color.DARK_YELLOW.format(username)} added"
        )

    def human_scroll(self, scrolling_time=60, scroll_pause_time=2):
        """Try to simulate a human scroll for infinite website
        Args:
            scrolling_time(int): the scrolling duration
            scrool_pause_tima(int): the paise time between each scroll
        """
        screen_height = self.browser.execute_script(
            "return window.screen.height;"
        )  # get the screen height of the web
        i = 1
        begin, end = 0, screen_height
        start_scrolling_time = time.time()
        while True:
            for e in range(begin, end, 216):
                for u in range(e, e + 216):
                    self.browser.execute_script(f"window.scrollTo(0, {u});")
                time.sleep(scroll_pause_time)
                # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
                scroll_height = self.browser.execute_script(
                    "return document.body.scrollHeight;"
                )
                # Break the loop when the height we need to scroll to is larger than the total scroll height

            current_scrolling_time = time.time()
            if (current_scrolling_time - start_scrolling_time) > scrolling_time:
                break
            if (
                screen_height * i > scroll_height
            ):  # check if we are in the end of the page
                break
            i = i + 1
            begin, end = end, screen_height * i

    def quit(self):
        """Quit the browser"""
        kill_process("firefox")
        self.clean_tmp_and_logs()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def get_cookies(self):
        pass
