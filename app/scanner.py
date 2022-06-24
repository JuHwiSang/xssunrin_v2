from typing import Optional

import requests
from app.utils.counter import Counter
from app.multidriver import Pool
from app.web import Link, Page
from app.logger import logger
import threading
import time



def scan(target: str, js_execution: bool = True, driver_pool: Optional[Pool] = None, driver_pool_size: int = 3):
    logger.debug("----------------- scanner start -----------------")
    visited = []
    to_visit = [Link(target)]
    counter = Counter()
    logger.debug(f"target: {target}")

    if js_execution:
        if driver_pool is None:
            own_driver_pool = True
            driver_pool = Pool(driver_pool_size)
        else:
            own_driver_pool = False

        def _request(link: Link):
            return driver_pool.request(link)

    else:
        def _request(link: Link):
            logger.info(f"{link.method} {link.uri} {link.data}")
            res = requests.request(link.method, link.url, params=link.params, data=link.data)
            return Page(link, res.text)

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
    #             logger.info(f"{link.method} {link.uri} {link.data}")
    #             res = requests.request(link.method, link.url, params=link.params, data=link.data)
    #             page = Page(link, res.text)
    #             links = page.parse_links()
    #             to_visit.extend(links)
    #         finally:
    #             counter.dec()
    #         # logger.debug(f"close thread: {link.url}")

    def _visit_and_push(link: Link):
        try:
            page = _request(link)
            links = page.parse_links()
            to_visit.extend(links)
        finally:
            counter.dec()

    
    try:
        while to_visit or not counter.iszero():
            if to_visit:
                link = to_visit.pop(0)
                if link in visited: #링크를 to_visit에 입력할 때, samedomain이나 valuable인지 등 다 체크해서 입력해야하네.
                    continue
                counter.inc()
                visited.append(link)
                threading.Thread(target=_visit_and_push, args=(link,), daemon=True).start()
            else:
                time.sleep(0.05)
    finally:
        if js_execution and own_driver_pool:
            driver_pool.quit()

    logger.debug("scanner end")
    return visited

# def is_samedomain()

# def is_sameurl(visited: list[Link], link: Link) -> bool:
#     return any


# if __name__ == "__main__":
#     # res = scan("http://139.150.74.9")
#     res = scan("http://cafe.naver.com", 3)