"""create script for follwers scrapping automation

Raises:
    er: if timeout or element not found

Returns:
    _type_: A folder contains all followers of the user based on scrolling time 
"""
import os
from seleniumwire import webdriver
from seleniumwire.utils import decode as sw_decode
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.firefox.options import Options
import time
import json
from random import randint

from models.driver import DRIVER_PATH

PROFILE_PATH = "/home/issam/PIXITREND-DRIVER-SOCIAL/src/ffprofile/edwardnewgate_4"
URL = "https://www.instagram.com/"
DELAY = 8
USERNAME = "edwardnewgate_4"
PASSWORD = "37004FB915"
USERNAME_SELECTOR = "input[name='username']"
PASSWORD_SELECTOR = "input[name='password']"
USER_FOR_SEARCH = "kooora"


def human_writing(selector, text):
    """Simulate human writing"""
    for x in text:
        selector.send_keys(x)
        time.sleep(randint(0, 1000) / 900)


# serach button for instagram users
def go_to_(user: str, browser: webdriver.Firefox):
    """Go to user page based on Xpath-Selector
    Args:
        user (str): username
    """
    browser.find_element(
        By.XPATH,
        "//div[@class='_aacl _aacp _aacu _aacx _aada'][normalize-space()='Search']",
    ).click()

    placeholder_selector = "input[placeholder='Search']"
    placeholder_element = browser.find_element(By.CSS_SELECTOR, placeholder_selector)
    human_writing(placeholder_element, user)

    for _ in range(3):
        try:
            first_appear = f"//div[@class='_aacl _aaco _aacw _aacx _aad6'][normalize-space()='{user}']"
            WebDriverWait(browser, DELAY).until(
                EC.presence_of_element_located((By.XPATH, first_appear))
            )
            browser.find_element(By.XPATH, first_appear).click()
            return
        except (TimeoutException, NoSuchElementException) as er:
            continue
    raise er


def human_scroll(browser, scrolling_time=60):
    # You can set your own pause time. My laptop is a bit slow so I use 1 sec
    scroll_pause_time = 2
    # get the screen height of the web
    screen_height = browser.execute_script("return window.screen.height;")
    i = 1
    begin, end = 0, screen_height
    start_scrolling_time = time.time()
    while True:
        for e in range(begin, end, 216):
            for u in range(e, e + 216):
                browser.execute_script(f"window.scrollTo(0, {u});")
            time.sleep(scroll_pause_time)
            # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
            scroll_height = browser.execute_script("return document.body.scrollHeight;")
            # Break the loop when the height we need to scroll to is larger than the total scroll height

        current_scrolling_time = time.time()
        if (current_scrolling_time - start_scrolling_time) > scrolling_time:
            break
        if screen_height * i > scroll_height:  # check if we are in the end of the page
            break
        i = i + 1
        begin, end = end, screen_height * i


def scroll_followers(browser, scroll_time: int = 60):
    start = time.time()
    pop_up_window = WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='_aano']"))
    )

    # Scroll till Followers list is there
    while True:
        browser.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;",
            pop_up_window,
        )
        time.sleep(1)
        current = time.time()
        if (current - start) > scroll_time:
            break
    print("Scrolling | End")


def login(browser: webdriver.Firefox, username: str, password: str):
    # process of logging if there is no cookies
    WebDriverWait(browser, DELAY).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, USERNAME_SELECTOR))
    )

    user_element = browser.find_element(By.CSS_SELECTOR, USERNAME_SELECTOR)
    human_writing(user_element, username)
    password_element = browser.find_element(By.CSS_SELECTOR, PASSWORD_SELECTOR)
    human_writing(password_element, password)
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()


def connected(browser: webdriver.Firefox) -> bool:
    """Check if user is connected"""
    for _ in range(3):
        try:
            WebDriverWait(browser, DELAY).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='_aacl _aacp _aacu _aacx _aada']")
                )
            )
            return True
        except TimeoutException:
            continue
    return False


def wait_til_loaded(browser: webdriver.Firefox, selector: str) -> bool:
    """Wait until page is loaded"""
    for _ in range(3):
        try:
            WebDriverWait(browser, DELAY).until(
                EC.presence_of_element_located((By.XPATH, selector))
            )
            return True
        except TimeoutException:
            continue
    return False


if __name__ == "__main__":
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("useAutomationExtension", False)
    # options.add_argument("excludeSwitches", ["enable-automation"])
    # options.add_argument("disable-infobars")
    # options.set_preference("general.useragent.override", user_agent)
    options.set_preference("dom.webnotifications.serviceworker.enabled", False)
    options.set_preference("dom.webnotifications.enabled", False)
    # options.set_preference("marionette", False)
    # options.set_preference("useAutomationExtension", False)
    # options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("network.proxy.type", 1)
    options.set_preference("profile.default_content_setting_values.notifications", 1)

    # proxy = get_env("PROXY")
    # if proxy:
    #     options.proxy = Proxy(
    #         {"proxyType": "MANUAL", "socksProxy": proxy, "socksVersion": 5}
    #     )

    if PROFILE_PATH:
        browser = webdriver.Firefox(
            options=options,
            firefox_profile=PROFILE_PATH,
            executable_path=DRIVER_PATH,
        )
    else:
        browser = webdriver.Firefox(options=options, executable_path=DRIVER_PATH)

    browser.get(URL)
    if not connected(browser):
        login(browser, USERNAME, PASSWORD)
    go_to_(USER_FOR_SEARCH, browser)
    wait_til_loaded(browser, f"//h2[normalize-space()='{USER_FOR_SEARCH}']")
    time.sleep(5)
    if USER_FOR_SEARCH in browser.current_url:
        browser.find_element(
            By.XPATH,
            f"//a[@href='/{USER_FOR_SEARCH}/followers/']//div[@class='_aacl _aacp _aacu _aacx _aad6 _aade']",
        ).click()
        wait_til_loaded(browser, "//div[contains(text(),'Followers')]")
        time.sleep(5)
        browser.find_element(By.XPATH, "//div[contains(text(),'Followers')]").click()

    # check if Only the user can see his followers list
    if not wait_til_loaded(browser, "//div[contains(@class,'_abab _abcm')]"):
        # Scroll followers Box
        scroll_followers(browser=browser, scroll_time=60)

    # TODO: If the account is private
    ...

    if not os.path.exists(USER_FOR_SEARCH):
        os.mkdir(f"{USER_FOR_SEARCH}_followers")

    # Access requests via the `requests` attribute
    batch = 0
    for request in browser.requests:
        if "follow_list_page" in request.url:
            data = sw_decode(
                request.response.body,
                request.response.headers.get("Content-Encoding", "identity"),
            )
            data = json.loads(data)
            with open(
                f"{USER_FOR_SEARCH}_followers/batch_{batch}.json", "w", encoding="utf-8"
            ) as f:
                json.dump(data, f, ensure_ascii=False)
            batch += 1

    browser.close()
    print("Process END")
