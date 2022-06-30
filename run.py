from app.scanner import scan
from app.attacker import xss
from app.multidriver import Pool
import argparse


def get_args():
    parser = argparse.ArgumentParser(description="To scan, and xss attack.")
    parser.add_argument("target", help="Target website")
    parser.add_argument("--driver-pool-size", type=int, help="Set selenium driver pool size.", default=3)
    parser.add_argument("--no-js", const=True, action="store_const", help="Use requests module instead selenium.", default=False)
    parser.add_argument("--xss-cheat-sheet", help="Set a cheat sheet file for xss.", default="./src/default_xss_cheat_sheet.txt")
    return parser.parse_args()


def main():
    args = get_args()
    target = args.target
    driver_pool_size = args.driver_pool_size
    usejs = not args.no_js
    xss_cheat_sheet = args.xss_cheat_sheet

    if usejs:
        pool = Pool(driver_pool_size)
    else:
        pool = None

    try:
        links = scan(target, driver_pool=pool, usejs=usejs)
        print("scan result:", links)
        succeed = xss(links, driver_pool=pool, usejs=usejs, cheat_sheet_path=xss_cheat_sheet)
        print("XSS result:", succeed)
    finally:
        if usejs:
            pool.quit()

if __name__ == "__main__":
    main()