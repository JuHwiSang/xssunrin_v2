from app.scanner import scan
from app.xss import reflected

target = "http://139.150.74.9"

links = scan(target)
print("scan result:", links)
succeed = reflected(links)
print("reflected result:", succeed)