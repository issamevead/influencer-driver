from contextlib import suppress
from random import randint

from dotenv import load_dotenv
from log.logger import Color, Logs
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.enums import PageId
from utils.util import get_env, get_profile_path, human_writing, json_extract

from models.driver import Driver

load_dotenv()

DELAY = int(get_env("DELAY"))
ROOT_PROFILE = get_env("FFPROFILE")

URL = "https://www.facebook.com/"
DELAY = 8


logs = Logs()


class Facebook(Driver):
    username: str
    password: str
    color: str
    USERNAME_SELECTOR: str = "#email"
    PASSWORD_SELECTOR: str = "#pass"
    CHECKER_SELECTOR: str = "a[aria-label='Home']"

    def __init__(
        self,
        username: str,
        password: str,
        proxy: str,
        color: Color = Color.LIGHTBLUE,
    ):
        profile_path = get_profile_path(ROOT_PROFILE, username)

        Driver.__init__(
            self,
            profile_path,
            proxy,
        )

        self.username = username
        self.password = password
        self.name = self.username.split("@")[0]
        self.blocked = False
        self.color = color
        if self.profile_path is None:
            self.profile_path = f"{ROOT_PROFILE}/{username}"
        for _ in range(3):
            try:
                self.browser.get(URL)
                break
            except WebDriverException as e:
                logs.error(e)
                continue

    def connect(self):
        timeout = DELAY
        for _ in range(3):
            with suppress(TimeoutException):
                WebDriverWait(self.browser, DELAY).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, self.USERNAME_SELECTOR)
                    )
                )
                user_element = self.browser.find_element(
                    By.CSS_SELECTOR, self.USERNAME_SELECTOR
                )
                user_element.clear()
                human_writing(user_element, self.username)
                password_element = self.browser.find_element(
                    By.CSS_SELECTOR, self.PASSWORD_SELECTOR
                )
                human_writing(password_element, self.password)
                self.browser.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                ).click()
                WebDriverWait(self.browser, timeout).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, self.CHECKER_SELECTOR)
                    )
                )
                logs.info(
                    f"{self.color.format(self.__class__.__name__)} | {Color.DARK_YELLOW.format(self.name)} connected successfully"
                )
                return True

            timeout += 2
            if (
                "checkpoint" in self.browser.current_url
                or "privacy_mutation_token" in self.browser.current_url
            ):
                self.blocked = True
                return False
        return False

    def is_connected(self):
        """Check if user is connected his facebook account
        Returns:
            bool: True if connected else False based on Cheacker Selector
        """
        timeout = DELAY
        for _ in range(3):
            with suppress(TimeoutException):
                WebDriverWait(self.browser, timeout).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, self.CHECKER_SELECTOR)
                    )
                )
                return True
            timeout += 2
        return False

    def get_cookies(self) -> str:
        """Get cookies from browser

        Returns:
            str: parsed cookies for requests and fb_dtsg for post request
        """
        EXPECTED_COOKIES = ("c_user", "xs", "datr")
        cookies = self.browser.get_cookies()
        names = json_extract(cookies, "name")
        values = json_extract(cookies, "value")
        initial_cookies = [f"{name}={value}" for name, value in zip(names, values)]

        cond = [name in names for name in EXPECTED_COOKIES]
        if not all(cond):
            return None
        with suppress(IndexError):
            body_contain_fb_dtsg = [
                b.body for b in self.browser.requests if b"fb_dtsg" in b.body
            ]
            fb_dtsg = [
                r for r in body_contain_fb_dtsg[0].decode().split("&") if "fb_dtsg" in r
            ][0]
            initial_cookies = initial_cookies + [fb_dtsg]
            return ";".join(initial_cookies)
        return None

    def run(self):
        """Run browser and connect to facebook
        >>> connect to facebook if cookies not settled
        >>> Update cookies in local folder and in mongodb
        >>> kill firfox process
        """
        if not self.is_connected():
            self.connect()
        if self.blocked:
            # TODO: handle blocked account
            logs.info(
                f"{self.color.format(self.__class__.__name__)} | {Color.DARK_YELLOW.format(self.name)} account is {Color.RED.format('blocked')}"
            )
            self.blocked_status(self.username)
            self.quit()
            return
        self.human_scroll(randint(45, 60), 2)
        self.update_local_cookie()
        self.update_mg_cookie(self.username, PageId.FACEBOOK.value)
        self.quit()
