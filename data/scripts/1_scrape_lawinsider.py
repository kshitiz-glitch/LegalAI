"""
Dataset 1a: LawInsider.com scraper — target 8,000 contracts
Output: data/raw/lawinsider/<contract_type>/<id>.json

Contract types + targets:
  nda                  -> 1,500
  employment-agreement -> 1,200
  service-agreement    -> 1,300
  saas-agreement       -> 1,000
  consulting-agreement -> 1,000
  vendor-agreement     -> 1,200
  lease-agreement      ->   800
"""
import json
import time
import uuid
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.lawinsider.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
DELAY = 3.0  # seconds between requests

CONTRACT_TARGETS = {
    "nda":                  1500,
    "employment-agreement": 1200,
    "service-agreement":    1300,
    "saas-agreement":       1000,
    "consulting-agreement": 1000,
    "vendor-agreement":     1200,
    "lease-agreement":       800,
}

# Map slug → search query for LawInsider's search endpoint
SEARCH_QUERIES = {
    "nda":                  "non-disclosure agreement",
    "employment-agreement": "employment agreement",
    "service-agreement":    "service agreement",
    "saas-agreement":       "software as a service agreement",
    "consulting-agreement": "consulting agreement",
    "vendor-agreement":     "vendor agreement",
    "lease-agreement":      "lease agreement",
}

OUTPUT_BASE = Path("data/raw/lawinsider")


def fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  fetch error {url}: {e}")
        return None


def scrape_contract_page(url: str) -> str | None:
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")

    for selector in [
        "div.contract-text", "div#contract-text", "div.document-content",
        "div.clause-text", "div#document", "div.document", "article",
        "div[class*='contract']", "div[class*='document']", "pre",
    ]:
        div = soup.select_one(selector)
        if div:
            text = div.get_text(separator=" ", strip=True)
            if len(text) > 300:
                return text
    return None


def get_contract_links(contract_type: str, page: int) -> list[tuple[str, str]]:
    """Returns list of (url, company_name) using LawInsider search endpoint."""
    query = SEARCH_QUERIES.get(contract_type, contract_type.replace("-", " "))
    from urllib.parse import quote_plus
    url = f"{BASE}/search?q={quote_plus(query)}&p={page}"
    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Try multiple result container selectors (site may vary)
    rows = (
        soup.select("div.search-result") or
        soup.select("li.search-result") or
        soup.select("div.contract-result") or
        soup.select("div[class*='result']")
    )

    for row in rows:
        # Try multiple link selectors
        link = (
            row.select_one("a[href*='/document']") or
            row.select_one("a[href*='/clause']") or
            row.select_one("h2 a") or
            row.select_one("h3 a") or
            row.select_one("a.title")
        )
        company = (
            row.select_one("span.company") or
            row.select_one("span.party") or
            row.select_one("div.company") or
            row.select_one("[class*='company']")
        )
        if link and link.get("href"):
            href = link["href"]
            if not href.startswith("http"):
                href = BASE + href
            company_name = company.get_text(strip=True) if company else "Unknown"
            results.append((href, company_name))

    return results


def scrape_contract_type(contract_type: str, target: int) -> int:
    out_dir = OUTPUT_BASE / contract_type
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = len(list(out_dir.glob("*.json")))
    if existing >= target:
        print(f"  {contract_type}: already have {existing} — skipping")
        return existing

    collected = existing
    page = 1

    while collected < target:
        print(f"  {contract_type} | page {page} | {collected}/{target}")
        links = get_contract_links(contract_type, page)

        if not links:
            print(f"  No more links on page {page}, stopping")
            break

        for url, company in links:
            if collected >= target:
                break

            text = scrape_contract_page(url)
            time.sleep(DELAY)

            if not text or len(text) < 500:
                continue

            contract_id = str(uuid.uuid4())[:8]
            filename = f"{contract_type}_{contract_id}.json"

            record = {
                "contract_id": contract_id,
                "source": "lawinsider",
                "contract_type": contract_type,
                "company": company,
                "url": url,
                "text": text,
                "word_count": len(text.split()),
            }

            (out_dir / filename).write_text(json.dumps(record, indent=2))
            collected += 1

        page += 1
        time.sleep(DELAY)

    return collected


def main():
    print("=== LawInsider Scraper ===")
    print(f"Target: {sum(CONTRACT_TARGETS.values())} contracts\n")

    total = 0
    for ct, target in CONTRACT_TARGETS.items():
        print(f"\n[{ct}] target={target}")
        n = scrape_contract_type(ct, target)
        total += n
        print(f"  Collected {n}")

    print(f"\n✅ Total collected: {total}")
    print(f"   Files in: {OUTPUT_BASE}/")


if __name__ == "__main__":
    main()
