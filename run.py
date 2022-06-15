from app.scanner import scan
from app.attacker import xss
from app.multidriver import Pool

target = "https://0a22003503855d6dc01953740020006f.web-security-academy.net/"
# target = "https://xss-game.appspot.com/level2/frame"

pool = Pool(3)
try:
    links = scan(target, driver_pool=pool)
    print("scan result:", links)
    succeed = xss(links, driver_pool=pool)
    print("XSS result:", succeed)
finally:
    pool.quit()
    ...