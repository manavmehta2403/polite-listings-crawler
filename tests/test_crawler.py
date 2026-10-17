from pathlib import Path
from crawler.crawl import Crawler
from crawler.parse import parse_listings
from crawler.politeness import RateLimiter, Robots, backoff

FX = Path(__file__).parent / "fixtures"
ROBOTS = "User-agent: *\nDisallow: /private\nCrawl-delay: 2\n"

class Clock:
    def __init__(self): self.t, self.slept = 0.0, []
    def now(self): return self.t
    def sleep(self, d): self.slept.append(d); self.t += d

def test_parse_reports_bad_cards_without_crashing():
    listings, errors, nxt = parse_listings((FX / "page1.html").read_text())
    assert [l.id for l in listings] == ["L1", "L2"]
    assert listings[1].nightly_price == 1050.5 and listings[1].rating is None
    assert errors == ["BAD: AttributeError"] and nxt == "/s?page=2"

def test_rate_limiter_spaces_requests_per_host():
    c = Clock(); rl = RateLimiter(2.0, c.now, c.sleep)
    rl.wait("https://a.test/1"); rl.wait("https://a.test/2"); rl.wait("https://b.test/1")
    assert c.slept == [2.0]

def test_robots_and_backoff():
    r = Robots(ROBOTS, "polite-bot")
    assert r.allowed("https://x.test/s") and not r.allowed("https://x.test/private/1")
    assert r.crawl_delay() == 2.0
    assert [backoff(i) for i in range(3)] == [0.5, 1.0, 2.0] and backoff(20) == 30.0

def test_crawl_paginates_retries_dedupes_and_respects_robots():
    pages = {"https://x.test/s": [(503, ""), (200, (FX / "page1.html").read_text())],
             "https://x.test/s?page=2": [(200, (FX / "page2.html").read_text())]}
    calls = []
    def fetch(url):
        calls.append(url); return pages[url].pop(0)
    c = Clock()
    cr = Crawler(fetch, Robots(ROBOTS, "polite-bot"), RateLimiter(1.0, c.now, c.sleep), sleep=c.sleep)
    result = cr.run("https://x.test/s")
    assert set(result) == {"L1", "L2", "L3"}
    assert result["L2"].nightly_price == 99.0
    assert cr.stats == {"pages": 2, "retries": 1, "skipped_robots": 1, "parse_errors": 1, "duplicates": 1}
    assert "https://x.test/private/page3" not in calls
