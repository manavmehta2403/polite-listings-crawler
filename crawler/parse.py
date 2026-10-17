from __future__ import annotations
import re
from dataclasses import dataclass
from bs4 import BeautifulSoup

@dataclass(frozen=True)
class Listing:
    id: str
    title: str
    city: str
    nightly_price: float
    currency: str
    rating: float | None

PRICE = re.compile(r"([€$£])\s?([\d,]+(?:\.\d+)?)")
CURRENCY = {"€": "EUR", "$": "USD", "£": "GBP"}

def parse_listings(html: str) -> tuple[list[Listing], list[str], str | None]:
    """Returns (listings, errors, next_page_url). A malformed card is reported, never crashes the page."""
    soup = BeautifulSoup(html, "html.parser")
    out, errors = [], []
    for card in soup.select("[data-listing-id]"):
        lid = card["data-listing-id"]
        try:
            m = PRICE.search(card.select_one(".price").get_text())
            rating_el = card.select_one(".rating")
            out.append(Listing(
                id=lid,
                title=card.select_one(".title").get_text(strip=True),
                city=card.select_one(".city").get_text(strip=True),
                nightly_price=float(m.group(2).replace(",", "")),
                currency=CURRENCY[m.group(1)],
                rating=float(rating_el.get_text(strip=True)) if rating_el else None,
            ))
        except (AttributeError, TypeError, ValueError, KeyError) as e:
            errors.append(f"{lid}: {type(e).__name__}")
    nxt = soup.select_one("a[rel=next]")
    return out, errors, nxt["href"] if nxt else None
