from typing import Callable, Optional

import requests
from app.utils.counter import Counter
from app.multidriver import Pool
from app.utils.helpers import requests_cookie_to_normal
from app.web import Link, Page
from app.logger import logger
import threading
import time



def scan(target: str, _request: Callable[[Link, dict[str, str]], Page], cookies: dict[str, str] = {}):
    logger.debug("----------------- scanner start -----------------")
    visited = []
    to_visit = [Link(target)]
    # counter = Counter()
    local_cookies: dict[str, str] = cookies.copy()

    logger.debug(f"target: {target}")
    logger.debug(f"initial cookies: {local_cookies}")

    # if usejs:
    #     if driver_pool is None:
    #         own_driver_pool = True
    #         driver_pool = Pool(driver_pool_size)
    #     else:
    #         own_driver_pool = False

    #     def _request(link: Link):
    #         page = driver_pool.request(link, cookies=local_cookies)
    #         local_cookies.update(page.cookies)
    #         return page

    # else:
    #     def _request(link: Link):
    #         logger.debug(f"{link.method} {link.uri} {link.data}")
    #         res = requests.request(link.method, link.url, params=link.params, data=link.data, cookies=local_cookies)
    #         local_cookies.update(requests_cookie_to_normal(res.cookies))
    #         return Page(link, res.text, cookies=res.cookies)

    #     def visit_and_push(link: Link):
    #         # logger.debug(f"{link.method} {link.uri}")
    #         # logger.debug(f"create thread: {link.url}")
    #         try:
    #             page = driver_pool.request(link)
    #             links = page.parse_links()
    #             to_visit.extend(links)
    #         finally:
    #             counter.dec()
    #         # logger.debug(f"close thread: {link.url}")
    # else:
    #     def visit_and_push(link: Link):
    #         # logger.debug(f"{link.method} {link.uri}")
    #         # logger.debug(f"create thread: {link.url}")
    #         try:
    #             logger.debug(f"{link.method} {link.uri} {link.data}")
    #             res = requests.request(link.method, link.url, params=link.params, data=link.data)
    #             page = Page(link, res.text)
    #             links = page.parse_links()
    #             to_visit.extend(links)
    #         finally:
    #             counter.dec()
    #         # logger.debug(f"close thread: {link.url}")

    def _visit_and_push(link: Link):
        try:
            # page = _request(link)
            # page = link.click(_request)
            page = _request(link, local_cookies)
            links = page.parse_links()
            local_cookies.update(page.cookies)
            to_visit.extend(links)
        finally:
            # counter.dec()
            ...

    threads: list[threading.Thread] = []
    def _thread_alive() -> bool:
        for thread in threads[:]:
            if thread.is_alive():
                return True
            else:
                threads.remove(thread)
        return False



    
    while to_visit or _thread_alive():
        if to_visit:
            # logger.debug(f"to_visit: {to_visit}")
            link = to_visit.pop(0)
            if link in visited: #링크를 to_visit에 입력할 때, samedomain이나 valuable인지 등 다 체크해서 입력해야하네.
                continue
            # counter.inc()
            visited.append(link)
            thread = threading.Thread(target=_visit_and_push, args=(link,), daemon=True)
            thread.start()
            threads.append(thread)
        else:
            time.sleep(0.05)

    logger.debug("scanner end")
    return visited

# def is_samedomain()

# def is_sameurl(visited: list[Link], link: Link) -> bool:
#     return any


# if __name__ == "__main__":
#     # res = scan("http://139.150.74.9")
#     res = scan("http://cafe.naver.com", 3)