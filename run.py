import requests
from app.scanner import scan
from app.attacker import xss
from app.multidriver import Pool, chrome_options_no_headless
from app.web import CSRF, Link, Page, parsecsrf

import json
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
        kwargs = {"chrome_options": chrome_options_no_headless}
    else:
        # print('check')
        kwargs = {}

    if usejs:
        pool = Pool(driver_pool_size, **kwargs)
        def _request(link: Link, cookies: dict[str, str], avoidcsrf: bool = True) -> Page:
            if avoidcsrf and link.iscsrf():
                params, data = _getcsrf(link, cookies)
                link = link.copy(params=params, data=data)
                page = pool.request(link, cookies=cookies)
                link.csrf.unlock()
            else:
                page = pool.request(link, cookies=cookies)
            return page
    else:
        def _request(link: Link, cookies: dict[str, str], avoidcsrf: bool = True) -> Page:
            if avoidcsrf and link.iscsrf():
                params, data = _getcsrf(link, cookies)
                link = link.copy(params=params, data=data)
                res = requests.request(link.method, link.url, params=link.params, data=link.data, cookies=cookies)
                page = Page(link, res.text, res.cookies)
                link.csrf.unlock()
            else:
                res = requests.request(link.method, link.url, params=link.params, data=link.data, cookies=cookies)
                page = Page(link, res.text, res.cookies)
            return page






    def _getcsrf(link: Link, cookies: dict[str, str]) -> CSRF:
        link.csrf.untilunlock()
        link.csrf.lock()
        page = _request(link.parent, cookies)
        return parsecsrf(page.source, link.csrf)




    try:
        links = scan(target, _request, cookies=cookies)
        print("scan result:", links)
        succeed = xss(links, _request, cheat_sheet_path=xss_cheat_sheet, cookies=cookies)
        print("XSS result:", succeed)
    finally:
        if usejs:
            pool.quit()

if __name__ == "__main__":
    main()