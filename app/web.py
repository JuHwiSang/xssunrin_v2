from turtle import st
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit
from bs4 import BeautifulSoup as bp

class CSRF:
    storage: str
    name: str
    token: str

    def __init__(self, storage, name, token="") -> None:
        self.storage = storage
        self.name = name
        self.token = token

class Link:
    url: str
    method: str
    params: dict[str, str]
    data: dict[str, str]
    parent: "Link"
    # csrf_token: tuple[str, str] | None
    csrf: Optional[CSRF]
    def __init__(self, url, method: str = "GET", parent: Optional["Link"] = None, params={}, data={}) -> None:
        # self.url = url
        splited = urlsplit(url)
        self.url = f"{splited[0]}://{splited[1]}{splited[2]}".lstrip("://")
        self.params = dict(parse_qsl(splited[3] + "&" + urlencode(params)))
        self.method = method.upper()
        self.parent = parent or self
        self.data = data
        self.csrf = check_csrf(self.params, self.data)


    def copy(self, params: dict[str, str] = {}, data: dict[str, str] = {}, token: str = "") -> "Link":
        new_link = Link(self.url, self.method, self.parent, {**self.params, **params}, {**self.data, **data})
        new_link.csrf.token = token
        return new_link

    @property
    def uri(self) -> str:
        return f"{self.url}?{urlencode(self.params)}".rstrip("?")
    
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Link):
            same_url = self.url == __o.url
            same_method = self.method == __o.method
            same_params = set(self.params.keys()) == set(__o.params.keys()) and set(self.data.keys()) == set(__o.data.keys())
            return same_url and same_method and same_params
        else:
            return self.url == str(__o)

    def __str__(self) -> str:
        return f"Link({self.url!r}, {self.method!r}, {self.params!r}, {self.data!r})"

    def __repr__(self) -> str:
        return str(self)

class Page:
    source: str
    link: Link
    alerts: list[str]

    def __init__(self, link, source, alerts=[]) -> None:
        self.source = source
        self.link = link
        self.alerts = alerts
    
    def parse_links(self) -> list[Link]:
        return [link
                for link in parse_links(self.source, self.link)
                if is_samedomain(self.link.url, link.url)]


dummy_data = {
    None: "dummy",
    "checkbox":"dummy",
    "color":"#ffffff",
    "date":"1990-01-01",
    "datetime-local":"1990-01-01T01:01",
    "email":"dummy@dummy.dummy",
    "file":"dummy.jpg",
    "hidden":"dummy",
    "month":"1990-01",
    "number":"1",
    "password":"dummy",
    "radio":"dummy",
    "search":"dummy",
    "tel":"000-0000-0000",
    "text":"dummy",
    "time":"01:01",
    "url":"https://dummy.dummy",
    "week":"1990-W01"
}

#May cause an issue by BeautifulSoup's parsing system: &param=3 -> ¶m=3
def parse_links(source: str, page_link: Link) -> list[Link]:
    soup = bp(source, 'html.parser')
    links = []
    
    # for tag_a in soup.find_all('a'):
    #     href = tag_a.get('href', None)
    #     if not(href is not None and is_valid_url(href)):
    #         continue
    #     url = urljoin(page_url, href)
    #     # url = href
    #     link = Link(url)
    #     links.append(link)
    a_href = tuple(map(lambda x: x.get('href', None), soup.find_all('a')))
    iframe_src = tuple(map(lambda x: x.get('src', None), soup.find_all('iframe')))
    for attr in a_href + iframe_src:
        # href = tag_a.get('href', None)
        if not(attr is not None and is_valid_url(attr)):
            continue
        url = urljoin(page_link.uri, attr)
        # url = href
        link = Link(url, parent=page_link)
        links.append(link)
    
    for tag_form in soup.find_all('form'):
        action = tag_form.get('action', "")
        method = tag_form.get('method', "GET").upper()
        url = urljoin(page_link.uri, action)
        # url = action
        inputs: dict[str, str] = {}
        for tag_input in (tag_form.find_all('input') + tag_form.find_all('textarea')):
            name = tag_input.get('name', None)
            type = tag_input.get('type', None)
            value = tag_input.get('value', None)
            if name is None:
                continue
            inputs[name] = value or dummy_data[type]

        if method == "GET":
            # link = Link(f"{url}?{attach_qs(inputs)}")
            link = Link(url, parent=page_link, params=inputs)
        elif method == "POST":
            link = Link(url, method, parent=page_link, data=inputs)
        else:
            continue
        links.append(link)
            
    return links

def is_valid_url(url: str) -> bool:
    return bool("".join(urlsplit(url)))

def is_samedomain(url1: str, url2: str) -> bool:
    return urlsplit(url1)[:2] == urlsplit(url2)[:2]

def check_csrf(params: dict[str, str], data: dict[str, str]) -> tuple[str, str] | None:
    for storage, key in [*map(lambda x:("GET", x), params.keys()), *map(lambda x:("POST", x), data.keys())]:
        if "csrf" in key:
            return CSRF(storage, key)
    else:
        return None