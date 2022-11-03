from contextlib import suppress
from random import randint
import time

from dotenv import load_dotenv
from log.logger import Logs, Color
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.enums import PageId
from utils.util import get_env, human_writing, get_profile_path, json_extract

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
    user_selector: str = "input[name='username']"
    password_selector: str = "input[name='password']"
    checker_selector: str = "//div[@class='_aac4 _aac5 _aac6']"

    def __init__(self, username: str, password: str, color: Color = Color.PURPLE):
        profile_path = get_profile_path(ROOTE_PROFILE, username)

        Driver.__init__(self, profile_path)
        self.username = username
        self.password = password
        self.color = color
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
        cookies = self.browser.get_cookies()
        names = json_extract(cookies, "name")
        values = json_extract(cookies, "value")
        return ";".join([f"{name}={value}" for name, value in zip(names, values)])

    def is_connected(self):
        timeout = DELAY
        for _ in range(3):
            with suppress(TimeoutException):
                WebDriverWait(self.browser, timeout).until(
                    EC.presence_of_element_located((By.XPATH, self.checker_selector))
                )
                return True
            timeout += 5
        return False

    def run(self):
        """Run Instagram ROBOT"""
        connected = self.is_connected()
        if not connected:
            self.connect()
        time.sleep(10)
        self.human_scroll(randint(45, 60), 2)
        self.update_local_cookie()
        self.update_mg_cookie(self.username, PageId.INSTAGRAM.value)
        self.quit()
