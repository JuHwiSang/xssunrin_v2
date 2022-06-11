from typing import Optional


class Counter():
    count: int
    step: int
    
    def __init__(self, start: int = 0, step: int = 1) -> None:
        self.count = start
        self.step = step

    def inc(self, step: Optional[int] = None) -> int:
        self.count += step or self.step
        return self.count

    def dec(self, step: Optional[int] = None) -> int:
        self.count -= step or self.step
        return self.count

    def iszero(self) -> bool:
        return not bool(self.count)