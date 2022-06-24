from typing import Optional

import requests
from app.utils.helpers import add_element_title, split_by_method, wait_until
from app.web import Link, Page
from app.logger import logger
from app.utils.counter import Counter
from app.multidriver import Pool
# from app.helpers import get_payloadlist
from bs4 import BeautifulSoup as bp
import threading
import re
import time


# payload_form = [
#     "<script>alert(10101{id}10101)</script>"
# ]
# payload_form = "<script>alert(10101{id}10101)</script>"
payload_form = "<script>alert('xssunrin{id}')</script>"
# payloadlist = get_payloadlist("./payloadlist.txt")
# payloadform = "10101{idx}10101"
# regex = re.compile("10101([0-9]+)10101")
payload_regex = re.compile("xssunrin([0-9]+)")
payload_regex_entire = re.compile("<script>alert\\(\\'xssunrin([0-9]+)\\'\\)</script>")
# regex.findall()
# regex.search(alert)
# regex.pattern

class colors:
    red = '\033[91m'
    endc = '\033[0m'

class AttackLog:
    type: str
    id: int
    link: Link
    # payload: dict[str, str]
    data_method: str
    param_name: str
    payload: str
    
    def __init__(self, type, id, link, data_method, param_name, payload) -> None:
        self.type = type
        self.id = id
        self.link = link
        self.data_method = data_method
        self.param_name = param_name
        self.payload = payload

    def __repr__(self) -> str:
        return f"AttackLog({self.type!r}, {self.id!r}, {self.link!r}, {self.data_method!r}, {self.param_name!r}, {self.payload!r})"

    def __str__(self) -> str:
        return repr(self)

    def alert(self) -> str:
        return f"{colors.red}{self.type}: {self.link.method} {self.link.uri} at {self.data_method} {self.param_name}, {self.payload}{colors.endc}"

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




def xss(links: list[Link], js_execution: bool = True, driver_pool: Optional[Pool] = None, driver_pool_size: int = 3) -> list[AttackLog]:
    logger.debug("----------------- XSS start -----------------")
    succeed = []
    attack_log: dict[int, AttackLog] = {}
    # visited = []
    # to_visit = [Link(target)]
    counter = Counter()

    # logger.debug(f"target: {target}")
    if js_execution:
        if driver_pool is None:
            own_driver_pool = True
            driver_pool = Pool(driver_pool_size)
        else:
            own_driver_pool = False

        def _request(link: Link):
            return driver_pool.request(link)
        def _is_xss(page: Page):
            for alert in page.alerts:
                searched = payload_regex.search(alert)
                if searched is not None:
                    id = int(searched.group(1))
                    return id
            return None

    else:
        def _request(link: Link):
            logger.debug(f"{link.method} {link.uri} {link.data}")
            res = requests.request(link.method, link.url, params=link.params, data=link.data)
            return Page(link, res.text)
        def _is_xss(page: Page):
            searched = payload_regex_entire.search(page.source)
            if searched is not None:
                id = int(searched.group(1))
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
            logger.debug(f"link: {link} {links}")
            it = add_element_title(("GET", "POST"), (link.params.keys(), link.data.keys()))
            for method, name in it:
                payload = payload_form.format(id=idx)
                params, data = split_by_method(method, name, payload)
                # if method == "GET":
                #     copy_link = link.copy(params={name: payload})
                # elif method == "POST":
                #     copy_link = link.copy(data={name: payload})
                # else:
                #     raise ValueError(f"Unknown method: {method}")
                copy_link = link.copy(params=params, data=data)
                attack_log[idx] = AttackLog("XSS", idx, copy_link, method, name, payload)
                counter.inc()
                threading.Thread(target=_visit_and_push, args=(copy_link,), daemon=True).start()
                idx += 1


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