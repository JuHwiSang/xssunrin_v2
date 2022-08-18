# Introduce
This is XSS vulnerability fuzzer.

yes, just, fuzzer.

Reflected XSS, Stored XSS..
If you use a great cheat sheet, maybe, also DOM XSS.

Blind XSS? Nope. It can't.


# Usage
```python3 run.py TARGET_URL```
- ```--driver-pool-size SIZE``` Set selenium driver pool size.
- ```--no-js``` Use requests module instead selenium.
- ```--xss-cheat-sheet PATH``` Set a cheat sheet file for xss.
- ```--cookies JSON``` Set initial cookies by json.
- ```--driver-show``` Show selenium window.


# Function
1. Fill empty input boxes.
2. Bypass pattern attribute.
3. Bypass csrf token.
4. Run Javascript.
5. Various payloads available.


# TODO
- add _is_xss argument