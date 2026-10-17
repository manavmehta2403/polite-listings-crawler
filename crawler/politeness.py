from __future__ import annotations
import time
from urllib import robotparser
from urllib.parse import urlparse

class RateLimiter:
    """Per-host minimum interval between requests (token-free, deterministic, clock injectable)."""
    def __init__(self, min_interval: float, clock=time.monotonic, sleep=time.sleep):
        self.min_interval, self.clock, self.sleep = min_interval, clock, sleep
        self._last: dict[str, float] = {}

    def wait(self, url: str) -> float:
        host = urlparse(url).netloc
        now = self.clock()
        delay = max(0.0, self._last.get(host, -1e9) + self.min_interval - now)
        if delay:
            self.sleep(delay)
        self._last[host] = now + delay
        return delay

class Robots:
    def __init__(self, robots_txt: str, user_agent: str):
        self.rp = robotparser.RobotFileParser()
        self.rp.parse(robots_txt.splitlines())
        self.ua = user_agent
    def allowed(self, url: str) -> bool:
        return self.rp.can_fetch(self.ua, url)
    def crawl_delay(self) -> float | None:
        d = self.rp.crawl_delay(self.ua)
        return float(d) if d else None

def backoff(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    return min(cap, base * 2 ** attempt)
