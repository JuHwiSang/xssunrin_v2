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