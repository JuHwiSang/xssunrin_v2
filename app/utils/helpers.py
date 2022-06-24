from typing import Any, Callable, Iterable
import time
# import random


def split_by_method(method, name, data):
    if method == "GET":
        return {name: data}, {}
    elif method == "POST":
        return {}, {name: data}
    else:
        ValueError(f"Unknown method: {method}")

def add_element_title(titles: Iterable[Any], elements: Iterable[Iterable[Any]]) -> list[tuple[Any, Any]]:
    ret = []
    for title, element in zip(titles, elements):
        ret.extend(map(lambda x:(title, x), element))
    return ret

def wait_until(func: Callable) -> None:
    while not func(): time.sleep(0.05)

def selenium_cookie_to_normal(selenium_cookies: list[dict[str, str]]) -> dict[str, str]:
    return {cookie['name'] : cookie['value'] for cookie in selenium_cookies}

def requests_cookie_to_normal(requests_cookies: Iterable[Any]) -> dict[str, str]:
    return {cookie.name : cookie.value for cookie in requests_cookies}

# def normal_to_selenium_add_cookies(normal_cookies: dict[str, str]) -> list[dict[str, str]]:
#     return [{'name': cookie['name'], 'value': cookie['value']} for cookie in normal_cookies]