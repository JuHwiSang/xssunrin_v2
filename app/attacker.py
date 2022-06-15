from typing import Optional
from app.web import Link
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
payload_form = "<script>alert(xssunrin{id})</script>"
# payloadlist = get_payloadlist("./payloadlist.txt")
# payloadform = "10101{idx}10101"
# regex = re.compile("10101([0-9]+)10101")
regex = re.compile("xssunrin([0-9]+)")
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


def xss(links: list[Link], driver_pool: Optional[Pool] = None, driver_pool_size: int = 3) -> list[AttackLog]:
    logger.debug("----------------- XSS start -----------------")
    succeed = []
    attack_log: dict[int, AttackLog] = {}
    # visited = []
    # to_visit = [Link(target)]
    counter = Counter()

    # logger.debug(f"target: {target}")
    if driver_pool is None:
        own_driver_pool = True
        driver_pool = Pool(driver_pool_size)
    else:
        own_driver_pool = False

    def find_csrf_token(link: Link) -> Link:
        page = driver_pool.request(link.parent_link)
        soup = bp(page.source, 'html.parser')
        token = soup.select_one(f"input[name={link.csrf_token[1]}]")['value']
        if link.csrf_token[0] == "GET":
            params, data = {**link.params, link.csrf_token[1]:token}, link.data
        elif link.csrf_token[0] == "POST":
            params, data = link.params, {**link.data, link.csrf_token[1]:token}
        return link.copy(params, data)

    def visit_and_push(link: Link):
        # logger.info(f"{link.method} {link.uri}")
        # logger.debug(f"create thread: {link.url}")
        try:
            if link.csrf_token:
                link = find_csrf_token(link)
            page = driver_pool.request(link)
            # logger.debug(f"page.alerts: {page.alerts}")
            for alert in page.alerts:
                searched = regex.search(alert)
                if searched is not None:
                    id = int(searched.group(1))
                    # AttackLog("xss_reflected", id, link, attack_try[id])
                    succeed.append(attack_log[id])
                    logger.info(attack_log[id].alert())
                    break
            # links = page.parse_links()
            # to_visit.extend(links)
        finally:
            counter.dec()
        # logger.debug(f"close thread: {link.url}")
    
    try:
        idx = 0
        for link in links:
            it = tuple(map(lambda x: ('GET', x), link.params)) + tuple(map(lambda x: ('POST', x), link.data))
            payload = payload_form.format(id=idx)
            for data_method, param_name in it:
                if data_method == "GET":
                    copy_link = link.copy(params={param_name: payload})
                elif data_method == "POST":
                    copy_link = link.copy(data={param_name: payload})
                else:
                    raise ValueError(f"Unknown method: {data_method}")
                attack_log[idx] = AttackLog("XSS", idx, copy_link, data_method, param_name, payload)
                counter.inc()
                threading.Thread(target=visit_and_push, args=(copy_link,), daemon=True).start()
                idx += 1

        #stored XSS 확인: 전체 다시 검사
        for link in links:
            counter.inc()
            threading.Thread(target=visit_and_push, args=(link,), daemon=True).start()

        while not counter.iszero():
            time.sleep(0.05)

    finally:
        if own_driver_pool:
            driver_pool.quit()

    logger.debug("XSS end")
    return succeed
    ...