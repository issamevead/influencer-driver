from copy import deepcopy
import time
from collections import deque
from contextlib import suppress
from random import randint
from typing import Tuple

from dotenv import load_dotenv
from log.logger import Color, Logs
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.enums import PageId
from utils.util import get_env, get_profile_path, human_writing
from models.driver import Driver

load_dotenv()
DELAY = int(get_env("DELAY"))
ROOTE_PROFILE = get_env("FFPROFILE")

URL = "https://www.instagram.com/accounts/login/"

logs = Logs()


class Instagram(Driver):
    username: str
    password: str
    color: Color
    dq: deque
    user_selector: str = "input[name='username']"
    password_selector: str = "input[name='password']"
    checker_selector: str = "//div[@class='_aac4 _aac5 _aac6']"

    def __init__(
        self,
        username: str,
        password: str,
        proxy: str,
        dq: deque,
        color: Color = Color.PURPLE,
    ):
        profile_path = get_profile_path(ROOTE_PROFILE, username)

        Driver.__init__(self, dq, profile_path, proxy)
        self.username = username
        self.password = password
        self.color = color
        self.blocked = False
        if self.profile_path is None:
            self.profile_path = f"{ROOTE_PROFILE}/{username}"
        for _ in range(3):
            try:
                self.browser.get(URL)
                return
            except WebDriverException as e:
                logs.error(e)
                continue

    def connect(self):
        timeout = DELAY
        for _ in range(3):

            if "/challenge/" in self.browser.current_url:
                self.blocked = True
                return False

            with suppress(TimeoutException):
                WebDriverWait(self.browser, DELAY).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, self.user_selector)
                    )
                )
                user_element = self.browser.find_element(
                    By.CSS_SELECTOR, self.user_selector
                )
                human_writing(user_element, self.username)
                password_element = self.browser.find_element(
                    By.CSS_SELECTOR, self.password_selector
                )
                human_writing(password_element, self.password)
                self.browser.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                ).click()
                WebDriverWait(self.browser, timeout).until(
                    EC.presence_of_element_located((By.XPATH, self.checker_selector))
                )
                logs.info(
                    f"{self.color.format('INSTAGRAM')} | {Color.DARK_YELLOW.format(self.username)} connected successfully"
                )
                return True
            timeout += 5
        return False

    def get_cookies(self):
        with suppress(IndexError):
            mitmdumps = deepcopy(self.mitmdumps)
            needed_call = [
                e
                for e in mitmdumps
                if "www.instagram.com" == e.request.authority
                and e.response.status_code == 200
            ][-1]
            if needed_call:
                content = needed_call.request.content.decode()
                method = needed_call.request.method
                url = needed_call.request.pretty_url
                headers = self.parse_headers(needed_call.request.headers.fields)
                return (headers, content, method, url)
        return (None, None, None, None)

    @staticmethod
    def parse_headers(headers: Tuple[tuple]):
        decoded_headers = [[e.decode() for e in header] for header in headers]
        cookies = ";".join([v for e, v in decoded_headers if e == "cookie"])
        converted_heads = dict(decoded_headers)
        converted_heads["cookie"] = cookies
        return converted_heads

    def is_connected(self):
        timeout = DELAY
        for _ in range(3):
            with suppress(TimeoutException):
                WebDriverWait(self.browser, timeout).until(
                    EC.presence_of_element_located((By.XPATH, self.checker_selector))
                )
                return True
            timeout += 5
            if "/challenge/" in self.browser.current_url:
                self.blocked = True
                return False
        return False

    def run(self):
        """Run Instagram ROBOT"""
        connected = self.is_connected()
        if not connected:
            self.connect()
        if self.blocked:
            # TODO: handle blocked account
            logs.info(
                f"{self.color.format(self.__class__.__name__)} | {Color.DARK_YELLOW.format(self.username)} account is {Color.RED.format('blocked')}"
            )
            self.blocked_status(self.username)
            self.quit()
            logs.info("Next update will until you unclock it")
            return
        # time.sleep(10)
        self.human_scroll(randint(45, 60), 2)
        self.update_local_cookie()
        self.update_mg_cookie(self.username, PageId.INSTAGRAM.value)
        self.quit()
