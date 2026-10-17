from __future__ import annotations
from typing import Callable
from urllib.parse import urljoin
from .parse import Listing, parse_listings
from .politeness import RateLimiter, Robots, backoff

Fetch = Callable[[str], tuple[int, str]]  # url -> (status, body)

class Crawler:
    def __init__(self, fetch: Fetch, robots: Robots, limiter: RateLimiter, max_pages: int = 50, max_retries: int = 3, sleep=None):
        self.fetch, self.robots, self.limiter = fetch, robots, limiter
        self.max_pages, self.max_retries = max_pages, max_retries
        self.sleep = sleep or limiter.sleep
        self.stats = {"pages": 0, "retries": 0, "skipped_robots": 0, "parse_errors": 0, "duplicates": 0}

    def _get(self, url: str) -> str | None:
        for attempt in range(self.max_retries + 1):
            self.limiter.wait(url)
            status, body = self.fetch(url)
            if status == 200:
                return body
            if status in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                self.stats["retries"] += 1
                self.sleep(backoff(attempt))
                continue
            return None
        return None

    def run(self, start_url: str) -> dict[str, Listing]:
        seen: dict[str, Listing] = {}
        url, visited = start_url, set()
        while url and url not in visited and self.stats["pages"] < self.max_pages:
            visited.add(url)
            if not self.robots.allowed(url):
                self.stats["skipped_robots"] += 1
                break
            body = self._get(url)
            if body is None:
                break
            self.stats["pages"] += 1
            listings, errors, nxt = parse_listings(body)
            self.stats["parse_errors"] += len(errors)
            for l in listings:
                if l.id in seen:
                    self.stats["duplicates"] += 1
                seen[l.id] = l
            url = urljoin(url, nxt) if nxt else None
        return seen
