from typing import Optional

import requests
from app.utils.helpers import add_element_title, requests_cookie_to_normal, split_by_method, wait_until
from app.web import Link, Page
from app.logger import logger
from app.utils.counter import Counter
from app.multidriver import Pool
# from app.helpers import get_payloadlist
from bs4 import BeautifulSoup as bp
import threading
import re
import time


DEFAULT_CHEAT_SHEET_PATH = "./src/default_cheat_sheet.txt"

# payload_form = [
#     "<script>alert(10101{id}10101)</script>"
# ]
# payload_form = "<script>alert(10101{id}10101)</script>"
# payload_form = "<script>alert('xssunrin{id}')</script>"
# payloadlist = get_payloadlist("./payloadlist.txt")
# payloadform = "10101{idx}10101"
# regex = re.compile("10101([0-9]+)10101")
alert_payload_regex = re.compile("xssunrin([0-9]+)")
# payload_regex_entire = re.compile("<script>alert\\(\\'xssunrin([0-9]+)\\'\\)</script>")
# regex.findall()
# regex.search(alert)
# regex.pattern

class AttackerError(Exception): pass
class DoubleAttackError(AttackerError): pass
class XSSError(AttackerError): pass

class colors:
    red = '\033[91m'
    endc = '\033[0m'

class AttackLog:
    type: str
    id: int
    link: Link
    # payload: dict[str, str]
    storage: str
    exploited_param_name: str
    payload: str
    
    def __init__(self, type, id, link, storage, exploited_param_name, payload) -> None:
        self.type = type
        self.id = id
        self.link = link
        self.storage = storage
        self.exploited_param_name = exploited_param_name
        self.payload = payload

    def __repr__(self) -> str:
        return f"AttackLog({self.type!r}, {self.id!r}, {self.link!r}, {self.storage!r}, {self.exploited_param_name!r}, {self.payload!r})"

    def __str__(self) -> str:
        return repr(self)

    def alert(self) -> str:
        return f"{colors.red}{self.type}: {self.link.method} {self.link.uri} at {self.storage} {self.exploited_param_name}, {self.payload}{colors.endc}"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, AttackLog):
            return (self.type == __o.type
                and self.link == __o.link
                and self.storage == __o.storage
                and self.exploited_param_name == __o.exploited_param_name)
        else:
            return NotImplemented

# class AttackResult:
#     type: str
#     id: int
#     link: Link
#     param_name: str
#     payload: str
#     def __init__(self, type, id, link, param_name, payload) -> None:
#         self.type = type
#         self.id = id
#         self.link = link
#         self.param_name = param_name
#         self.payload = payload


def read_cheat_sheet(cheat_sheet_path: str):
    with open(cheat_sheet_path, "r") as f:
        forms = f.readlines()
        for form in forms:
            if "{mark}" not in form:
                raise ValueError(f"{{mark}} not in form: {form}")
        forms = tuple(map(lambda x:x.replace("{mark}", "xssunrin{id}"), forms))
        regexs = tuple(re.compile(re.escape(line).replace("\\{id\\}", "([0-9]+)")) for line in forms)
        return forms, regexs

def find_payload_id(regex: re.Pattern, text: str) -> int | None:
    searched = regex.search(text)
    if searched is not None:
        id = int(searched.group(1))
        return id

def xss(links: list[Link], js_execution: bool = True, driver_pool: Optional[Pool] = None, driver_pool_size: int = 3, cheat_sheet_path: Optional[str] = None) -> list[AttackLog]:

    if cheat_sheet_path is None:
        raise ValueError("No cheat sheet selected.")

    logger.debug("----------------- XSS start -----------------")
    succeed: list[AttackLog] = []
    attack_log: dict[int, AttackLog] = {}
    # visited = []
    # to_visit = [Link(target)]
    counter = Counter()
    local_cookies: dict[str, str] = {}

    # def _add_local_cookies(cookies: dict[str, str]) -> None:
    #     for cookie in cookies:
    #         if cookie not in local_cookies:
    #             local_cookies.append(cookie)

    # logger.debug(f"target: {target}")

    payload_forms, payload_regexs = read_cheat_sheet(cheat_sheet_path)
    if js_execution:
        if driver_pool is None:
            own_driver_pool = True
            driver_pool = Pool(driver_pool_size)
        else:
            own_driver_pool = False

        def _request(link: Link):
            page = driver_pool.request(link, cookies=local_cookies)
            # _add_local_cookies(page.cookies)
            local_cookies.update(page.cookies)
            return page
        def _is_xss(page: Page):
            for alert in page.alerts:
                # searched = alert_payload_regex.search(alert)
                # if searched is not None:
                #     id = int(searched.group(1))
                #     return id
                id = find_payload_id(alert_payload_regex, alert)
                if id:
                    return id
            return None

    else:
        def _request(link: Link):
            logger.debug(f"{link.method} {link.uri} {link.data}")
            res = requests.request(link.method, link.url, params=link.params, data=link.data, cookies=local_cookies)
            # _add_local_cookies(map(lambda x:{'name':x.name, 'value':x.value}, res.cookies))
            local_cookies.update(requests_cookie_to_normal(res.cookies))
            return Page(link, res.text, cookies=local_cookies)
        def _is_xss(page: Page):
            # searched = payload_regex_entire.search(page.source)
            # if searched is not None:
            #     id = int(searched.group(1))
            #     return id
            for regex in payload_regexs:
                id = find_payload_id(regex, page.source)
                if id:
                    return id
            return None
            

    # def find_csrf_token(link: Link) -> Link:
    #     page = driver_pool.request(link.parent)
    #     soup = bp(page.source, 'html.parser')
    #     token = soup.select_one(f"input[name={link.csrf_token[1]}]")['value']
    #     if link.csrf_token[0] == "GET":
    #         params, data = {**link.params, link.csrf_token[1]:token}, link.data
    #     elif link.csrf_token[0] == "POST":
    #         params, data = link.params, {**link.data, link.csrf_token[1]:token}
    #     return link.copy(params, data)

    # def _set_csrf_token(link: Link):
    #     page = _request(link)
    #     soup = bp(page.source, 'html.parser')
    #     token = soup.select_one(f"input[name={link.csrf.name}]")['value']
    #     # link.csrf.token = token
    #     if link.csrf.method == "GET":
    #         params, data = {**link.params, link.csrf.name:token}, link.data
    #     elif link.csrf.method == "POST":
    #         params, data = link.params, {**link.data, link.csrf.name:token}
    #     return link.copy(params, data, token=token)

    def _visit_and_push(link: Link):
        # logger.debug(f"{link.method} {link.uri}")
        # logger.debug(f"create thread: {link.url}")
        try:
            # if link.csrf_token:
            #     link = find_csrf_token(link)
            # link.set_csrf_token(_request)
            # link = link.set_csrf_token()
            # page = driver_pool.request(link)
            # page = _request(link)
            page = link.click(_request)
            # logger.debug(f"page.alerts: {page.alerts}")
            xss_log_id = _is_xss(page)
            if xss_log_id:
                if xss_log_id not in attack_log:
                    raise DoubleAttackError(f"This attacker already attacked this website, and succeed.(log id: {xss_log_id}")
                elif attack_log[xss_log_id] not in succeed:
                    succeed.append(attack_log[xss_log_id])
                    logger.debug(attack_log[xss_log_id].alert())
            # for alert in page.alerts:
            #     searched = regex.search(alert)
            #     if searched is not None:
            #         id = int(searched.group(1))
            #         # AttackLog("xss_reflected", id, link, attack_try[id])
            #         succeed.append(attack_log[id])
            #         logger.debug(attack_log[id].alert())
            #         break
            # links = page.parse_links()
            # to_visit.extend(links)
        finally:
            counter.dec()
        # logger.debug(f"close thread: {link.url}")
    
    try:
        idx = 0
        for link in links:
            # logger.debug(f"link: {link} {links}")
            it = add_element_title(("GET", "POST"), (link.params.keys(), link.data.keys()))
            for method, name in it:
                # payload = payload_form.format(id=idx)
                for payload_form in payload_forms:
                    payload = payload_form.format(id=idx)
                    params, data = split_by_method(method, {name: payload})
                    # if method == "GET":
                    #     copy_link = link.copy(params={name: payload})
                    # elif method == "POST":
                    #     copy_link = link.copy(data={name: payload})
                    # else:
                    #     raise ValueError(f"Unknown method: {method}")
                    copy_link = link.copy(params=params, data=data)
                    attack_log[idx] = AttackLog("XSS", idx, copy_link, method, name, payload)
                    idx += 1
                    counter.inc()
                    threading.Thread(target=_visit_and_push, args=(copy_link,), daemon=True).start()


        # while not counter.iszero():
        #     time.sleep(0.05)
        wait_until(lambda:counter.iszero())

        #stored XSS 확인: 전체 다시 검사
        for link in links:
            counter.inc()
            threading.Thread(target=_visit_and_push, args=(link,), daemon=True).start()

        # while not counter.iszero():
        #     time.sleep(0.05)
        wait_until(lambda:counter.iszero())

    finally:
        if js_execution and own_driver_pool:
            driver_pool.quit()

    logger.debug("XSS end")
    return succeed
    ...