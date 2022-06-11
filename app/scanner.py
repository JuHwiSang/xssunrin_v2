from app.utils.counter import Counter
from app.multidriver import Pool
from app.web import Link
from app.logger import logger
import threading
import time



def scan(target: str, driver_pool_size: int = 3):
    logger.debug("scanner start")
    visited = []
    to_visit = [Link(target)]
    counter = Counter()

    logger.debug(f"target: {target}")
    logger.debug(f"driver_pool_size: {driver_pool_size}")

    logger.debug("driver pool loading...")
    driverpool = Pool(driver_pool_size)
    logger.debug("succeed.")

    def visit_and_push(link: Link):
        # logger.debug(f"{link.method} {link.uri}")
        # logger.debug(f"create thread: {link.url}")
        page = driverpool.request(link)
        links = page.parse_links()
        to_visit.extend(links)
        counter.dec()
        # logger.debug(f"close thread: {link.url}")
    
    while to_visit or not counter.iszero():
        if to_visit:
            link = to_visit.pop(0)
            if link in visited: #링크를 to_visit에 입력할 때, samedomain이나 valuable인지 등 다 체크해서 입력해야하네.
                continue
            counter.inc()
            visited.append(link)
            threading.Thread(target=visit_and_push, args=(link,), daemon=True).start()
        else:
            time.sleep(0.05)

    logger.debug("driver pool closing...")
    driverpool.quit()
    logger.debug("succeed.")

    logger.debug("scanner end")
    return visited

# def is_samedomain()

# def is_sameurl(visited: list[Link], link: Link) -> bool:
#     return any


if __name__ == "__main__":
    # res = scan("http://139.150.74.9")
    res = scan("http://cafe.naver.com", 3)