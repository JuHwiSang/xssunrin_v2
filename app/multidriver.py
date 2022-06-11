from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app.web import Link, Page
from app.logger import logger
import time
import os
os.environ['WDM_LOG'] = '50'

from logging import CRITICAL

# chrome_path = "./chrome/chromedriver.exe"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_path = ChromeDriverManager().install()


def create_send_script(method: str, url: str, data: dict[str, str]) -> str:
    form = 'document.write(`'
    form += f'<form id="exec" action="{url}" method="{method}">'
    for name, value in data.items():
        form += f'<input name="{name}" value="{value}">'
    form += "</form>"
    form += "`);document.getElementById('exec').submit();"
    return form


class Driver():
    driver: Chrome
    occupied: bool

    def __init__(self) -> None:
        self.driver = Chrome(executable_path=chrome_path, chrome_options=chrome_options)
        self.occupied = False

    def request(self, link: Link) -> Page:
        if link.method == "GET":
            self.driver.get(link.uri)
        else:
            self.driver.get("data:")
            self.driver.execute_script(create_send_script(link.method, link.uri, link.data))
        self.driver.implicitly_wait(5)
        alerts = self.get_alerts()
        page = Page(link, self.driver.page_source, alerts)
        return page

    def get_alerts(self) -> list[str]:
        alerts = []
        while 1:
            try:
                alert = self.driver.switch_to.alert
                alerts.append(alert.text)
                alert.accept()
            except NoAlertPresentException:
                return alerts

    def quit(self) -> None:
        self.driver.quit()

    def use(self) -> None:
        self.occupied = True

    def free(self) -> None:
        self.occupied = False

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
        self.pool = [Driver() for _ in range(size)]

    # def requests(self, links: list[Link]) -> None:
    #     for link in links:
    #         self.request(link)

    def request(self, link: Link) -> Page:
        logger.info(f"{link.method} {link.uri} {link.data}")
        with self.get_usable_driver() as driver:
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
        for driver in self.pool:
            driver.quit()


def show(link: Link) -> None:
    # driver = Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)
    driver = Driver()
    with driver:
        driver.request(link)