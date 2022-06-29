import os

from app.utils.helpers import selenium_cookie_to_normal
os.environ['WDM_LOG'] = '50'

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app.web import Link, Page
from app.logger import logger
import time


# chrome_path = "./chrome/chromedriver.exe"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options_no_headless = Options()
chrome_options_no_headless.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_path = ChromeDriverManager().install()


def create_send_script(method: str, url: str, data: dict[str, str]) -> str:
    # form = 'document.write(`'
    form = f'<form id="exec" action={url!r} method={method!r}>'
    value_inject_script = ""
    for name, value in data.items():
        form += f'<input name={name!r}>'
        value_inject_script += f"document.querySelector(`input[name={name!r}]`).value={value!r};"
    form += "</form>"
    script = f"document.write(`{form}`);{value_inject_script};document.getElementById('exec').submit();"
    # form += "`);document.getElementById('exec').submit();"
    return script


class Driver(Chrome):
    # driver: Chrome
    occupied: bool
    havnt_requested: bool

    # def __init__(self) -> None:
    #     self.driver = Chrome(executable_path=chrome_path, chrome_options=chrome_options)
    #     self.occupied = False
    def __init__(self, *args, **kwargs):
        self.occupied = False
        self.havnt_requested = True
        default_kwargs = {"executable_path" : chrome_path, "chrome_options" : chrome_options}
        default_kwargs.update(kwargs)
        super().__init__(*args, **default_kwargs)

    def request(self, link: Link) -> Page:
        if link.method == "GET":
            self.get(link.uri)
        else:
            self.get("data:")
            self.execute_script(create_send_script(link.method, link.uri, link.data))
        self.implicitly_wait(5)
        # if link.method == "POST": logger.debug(f"post link: {link.uri}, currernt_path: {self.current_url}")
        # self.execute_script("alert('um?');") #test
        alerts = self.get_alerts()
        page = Page(link, self.page_source, alerts, selenium_cookie_to_normal(self.get_cookies()))
        return page

    def get_alerts(self) -> list[str]:
        alerts = []
        while 1:
            try:
                alert = self.switch_to.alert
                # self.switch_to.active_element
                # self.switch_to.
                alerts.append(alert.text)
                alert.accept()
            except NoAlertPresentException:
                return alerts

    def add_cookies(self, cookies: dict[str, str]) -> None:
        for key, value in cookies.items():
            try:
                self.add_cookie({'name' : key, 'value' : value})
            except:
                print("url:", self.current_url)
                print("driver cookies:", self.get_cookies())
                print("cookies:", cookies)
                print("current_cookie:", key, value)
                raise

    def init_first_request(self, link: Link) -> None:
        if self.havnt_requested:
            self.get(link.url_without_path)
            self.implicitly_wait(5)
            self.havnt_requested = False

    # def quit(self) -> None:
    #     self.driver.quit()

    def use(self) -> None:
        self.occupied = True

    def free(self) -> None:
        self.occupied = False

    def __enter__(self):
        return super().__enter__()

    def __enter__(self) -> "Driver":
        self.use()
        return self

    def __exit__(self, *a, **kw) -> None:
        self.free()

#다중스레드 혹은 비동기 요청에만 실질적인 효과가 있도록 설계됨
class Pool():
    size: int
    pool: list[Driver]
    # threads: dict[Link, ThreadingResult]

    def __init__(self, size: int = 3) -> None:
        self.size = size
        logger.debug(f"Driver pool({size}) is loading...")
        self.pool = [Driver() for _ in range(size)]
        logger.debug("Driver pool loading succeed.")

    # def requests(self, links: list[Link]) -> None:
    #     for link in links:
    #         self.request(link)

    def request(self, link: Link, cookies: dict[str, str] = {}) -> Page:
        logger.debug(f"{link.method} {link.uri} {link.data}")
        with self.get_usable_driver() as driver:
            driver.init_first_request(link)
            driver.add_cookies(cookies)
            return driver.request(link)
        # driver.use()
        # def close_after_use():
        #     res = driver.request(link)
        #     driver.free()
        #     return res
        # thread = ThreadingResult(close_after_use)
        # thread.start()
        # self.threads[link] = thread

        # 여기 with로 세션열고 실행시키면 됨..잠깐, 그럼 threading이 안되자나, 좀 다른걸로 해야할듯.

    def get_usable_driver(self) -> Driver:
        while 1:
            for driver in self.pool:
                if not driver.occupied:
                    driver.use()
                    return driver
            time.sleep(0.05)

    def quit(self) -> None:
        logger.debug("Driver pool is closing...")
        for driver in self.pool:
            driver.quit()
        logger.debug("Driver pool closing succeed.")


def show(link: Link, block: bool = True) -> Page:
    # driver = Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)
    driver = Driver(chrome_options=chrome_options_no_headless)
    page = driver.request(link)
    print('out!')
    if block: input("press enter to continue...")
    return page