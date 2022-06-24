from app.scanner import scan
from app.attacker import xss
from app.multidriver import Pool
import argparse


def get_args():
    parser = argparse.ArgumentParser(description="To scan, and xss attack.")
    parser.add_argument("target", help="Target website")
    parser.add_argument("--driver-pool-size", type=int, help="Set Driver Pool size.", default=3)
    parser.add_argument("--no-js", const=True, action="store_const", help="Use 'requests' instead 'selenium'.", default=False)
    # parser.add_argument("--xss-cheat-sheet", help="Set a cheat sheet file for xss.")
    return parser.parse_args()


def main():
    args = get_args()
    target = args.target
    driver_pool_size = args.driver_pool_size
    use_js_execution = not args.no_js

    if use_js_execution:
        pool = Pool(driver_pool_size)
    else:
        pool = None

    try:
        links = scan(target, driver_pool=pool, js_execution=use_js_execution)
        print("scan result:", links)
        succeed = xss(links, driver_pool=pool, js_execution=use_js_execution)
        print("XSS result:", succeed)
    finally:
        if use_js_execution:
            pool.quit()

if __name__ == "__main__":
    main()