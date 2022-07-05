import json
from app.scanner import scan
from app.attacker import xss
from app.multidriver import Pool, chrome_options_no_headless
import argparse


def get_args():
    parser = argparse.ArgumentParser(description="To scan, and xss attack.")
    parser.add_argument("target", help="Target website")
    parser.add_argument("--driver-pool-size", type=int, help="Set selenium driver pool size.", default=3)
    parser.add_argument("--no-js", action="store_true", help="Use requests module instead selenium.", default=False)
    parser.add_argument("--xss-cheat-sheet", help="Set a cheat sheet file for xss.", default="./src/default_xss_cheat_sheet.txt")
    parser.add_argument("--cookies", help="Set initial cookies by json.", type=json.loads, default={})
    parser.add_argument("--driver-show", help="Show selenium window.", action="store_true", default=False)
    return parser.parse_args()


def main():
    args = get_args()
    target = args.target
    driver_pool_size = args.driver_pool_size
    usejs = not args.no_js
    xss_cheat_sheet = args.xss_cheat_sheet
    cookies = args.cookies
    driver_show = args.driver_show

    if driver_show:
        kwargs = {"driver_options": chrome_options_no_headless}
    else:
        kwargs = {}

    if usejs:
        pool = Pool(driver_pool_size, **kwargs)
    else:
        pool = None

    try:
        links = scan(target, driver_pool=pool, usejs=usejs, cookies=cookies)
        print("scan result:", links)
        succeed = xss(links, driver_pool=pool, usejs=usejs, cheat_sheet_path=xss_cheat_sheet, cookies=cookies)
        print("XSS result:", succeed)
    finally:
        if usejs:
            pool.quit()

if __name__ == "__main__":
    main()