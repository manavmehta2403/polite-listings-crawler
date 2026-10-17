# polite-listings-crawler

A small, well-behaved crawler for paginated listing pages (stays, rentals, marketplaces) — built to show the boring parts that make a crawler safe to run: **robots.txt, per-host rate limiting, retry with exponential backoff, tolerant parsing and de-duplication**.

Ships with synthetic HTML fixtures only. Point it only at sites whose terms allow automated access.

## Features
- `Robots` — honours `Disallow` and `Crawl-delay`
- `RateLimiter` — minimum interval per host, injectable clock (fully deterministic tests)
- Retries on 429/5xx with capped exponential backoff; gives up cleanly on 4xx
- Parser reports malformed cards as errors instead of crashing the page
- De-duplicates listings across pages (latest wins) and stops at robots-disallowed or already-visited pages
- Crawl stats: pages, retries, robots skips, parse errors, duplicates

## Run
```bash
pip install -r requirements.txt
pytest -q
```
`fetch` is injected (`url -> (status, body)`), so swapping in `httpx`, `requests` or Playwright is one function.

MIT licensed.
