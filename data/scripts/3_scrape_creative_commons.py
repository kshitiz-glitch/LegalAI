"""
Dataset 1c: Creative Commons legal forms — target 2,000 contracts
Sources:
  - Docracy.com        (~800) — CC-licensed user-uploaded contracts
  - OneCLE.com         (~700) — free legal form library
  - GitHub legal repos (~500) — YC SAFE, open-source templates

Output: data/raw/creative_commons/<id>.json
"""
import json
import re
import time
import uuid
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT = Path("data/raw/creative_commons")
OUTPUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LegalAI-Research/1.0)"}
DELAY = 2.0

# ─────────────────────────────────────────────
# Source 1: Docracy.com
# ─────────────────────────────────────────────

DOCRACY_BASE = "https://www.docracy.com"
DOCRACY_SEARCH_URLS = [
    "/doc/search?q=agreement&page={page}",
    "/doc/search?q=contract&page={page}",
    "/doc/search?q=nda&page={page}",
    "/doc/search?q=employment&page={page}",
]


def scrape_docracy(target: int = 800) -> int:
    collected = 0
    for search_path in DOCRACY_SEARCH_URLS:
        if collected >= target:
            break
        for page in range(1, 50):
            if collected >= target:
                break
            url = DOCRACY_BASE + search_path.format(page=page)
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                links = soup.select("a[href*='/doc/']")
                if not links:
                    break

                for link in links:
                    if collected >= target:
                        break
                    href = link.get("href", "")
                    if not re.match(r"/doc/\d+", href):
                        continue

                    doc_url = DOCRACY_BASE + href
                    try:
                        dr = requests.get(doc_url, headers=HEADERS, timeout=15)
                        dsoup = BeautifulSoup(dr.text, "html.parser")
                        content = dsoup.select_one("div#doc-content, div.doc-text, pre")
                        if not content:
                            continue
                        text = content.get_text(separator=" ", strip=True)
                        if len(text) < 300:
                            continue

                        record = {
                            "contract_id": str(uuid.uuid4())[:8],
                            "source": "docracy",
                            "contract_type": "general",
                            "company": "Unknown",
                            "url": doc_url,
                            "text": text[:80000],
                            "word_count": len(text.split()),
                            "license": "CC",
                        }
                        (OUTPUT / f"docracy_{record['contract_id']}.json").write_text(
                            json.dumps(record, indent=2)
                        )
                        collected += 1
                        time.sleep(DELAY)
                    except Exception:
                        pass

            except Exception as e:
                print(f"  Docracy page error: {e}")
            time.sleep(DELAY)

    print(f"  Docracy: {collected}")
    return collected


# ─────────────────────────────────────────────
# Source 2: OneCLE.com
# ─────────────────────────────────────────────

ONECLE_CATEGORIES = [
    "https://www.onecle.com/forms/employment/",
    "https://www.onecle.com/forms/nondisclosure/",
    "https://www.onecle.com/forms/service/",
    "https://www.onecle.com/forms/partnership/",
    "https://www.onecle.com/forms/license/",
    "https://www.onecle.com/forms/consulting/",
    "https://www.onecle.com/forms/vendor/",
]


def scrape_onecle(target: int = 700) -> int:
    collected = 0
    for cat_url in ONECLE_CATEGORIES:
        if collected >= target:
            break
        try:
            r = requests.get(cat_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            links = [a["href"] for a in soup.select("a[href]") if ".html" in a.get("href", "")]

            for href in links[:50]:
                if collected >= target:
                    break
                try:
                    url = href if href.startswith("http") else "https://www.onecle.com" + href
                    pr = requests.get(url, headers=HEADERS, timeout=15)
                    psoup = BeautifulSoup(pr.text, "html.parser")
                    content = psoup.select_one("div#contract, div.contract-text, div#content")
                    if not content:
                        continue
                    text = content.get_text(separator=" ", strip=True)
                    if len(text) < 300:
                        continue

                    record = {
                        "contract_id": str(uuid.uuid4())[:8],
                        "source": "onecle",
                        "contract_type": cat_url.split("/")[-2],
                        "company": "Template",
                        "url": url,
                        "text": text[:80000],
                        "word_count": len(text.split()),
                        "license": "free_access",
                    }
                    (OUTPUT / f"onecle_{record['contract_id']}.json").write_text(
                        json.dumps(record, indent=2)
                    )
                    collected += 1
                    time.sleep(DELAY)
                except Exception:
                    pass
        except Exception as e:
            print(f"  OneCLE category error: {e}")

    print(f"  OneCLE: {collected}")
    return collected


# ─────────────────────────────────────────────
# Source 3: GitHub legal repos
# ─────────────────────────────────────────────

GITHUB_REPOS = [
    # YC documents
    ("ycombinator", "documents", ["*.md", "*.txt"]),
    # Common legal templates
    ("commonpaper", "common-paper", ["*.md"]),
    # Open source legal
    ("github", "open-source-survey", ["*.md"]),
    # Bonterms open contracts
    ("bonterms", "bonterms", ["*.md", "*.txt"]),
    # NVCA model legal docs
    ("nvca-model-legal-docs", "nvca", ["*.md"]),
]

GITHUB_API = "https://api.github.com"
GH_HEADERS = {**HEADERS, "Accept": "application/vnd.github.v3+json"}


def scrape_github(target: int = 500) -> int:
    collected = 0

    # Curated raw URLs for known legal repos
    raw_urls = [
        "https://raw.githubusercontent.com/CommonPaper/standard/main/common-paper-csa-saas-v1.0.md",
        "https://raw.githubusercontent.com/bonterms/bonterms/main/Cloud-Service-Agreement.md",
        "https://raw.githubusercontent.com/bonterms/bonterms/main/Data-Processing-Agreement.md",
        "https://raw.githubusercontent.com/bonterms/bonterms/main/Professional-Services-Agreement.md",
        "https://raw.githubusercontent.com/bonterms/bonterms/main/Non-Disclosure-Agreement.md",
    ]

    for url in raw_urls:
        if collected >= target:
            break
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            text = r.text
            if len(text) < 300:
                continue

            record = {
                "contract_id": str(uuid.uuid4())[:8],
                "source": "github",
                "contract_type": "open_source_template",
                "company": "Open Source",
                "url": url,
                "text": text[:80000],
                "word_count": len(text.split()),
                "license": "CC",
            }
            (OUTPUT / f"github_{record['contract_id']}.json").write_text(
                json.dumps(record, indent=2)
            )
            collected += 1
            time.sleep(1)
        except Exception as e:
            print(f"  GitHub url error: {e}")

    # Search GitHub for more legal templates
    search_url = f"{GITHUB_API}/search/repositories?q=legal+contract+template&sort=stars&per_page=20"
    try:
        r = requests.get(search_url, headers=GH_HEADERS, timeout=15)
        repos = r.json().get("items", [])
        for repo in repos:
            if collected >= target:
                break
            owner = repo["owner"]["login"]
            name = repo["name"]
            # Get README
            readme_url = f"https://raw.githubusercontent.com/{owner}/{name}/main/README.md"
            try:
                rr = requests.get(readme_url, headers=HEADERS, timeout=10)
                if rr.status_code == 200 and len(rr.text) > 500:
                    record = {
                        "contract_id": str(uuid.uuid4())[:8],
                        "source": "github",
                        "contract_type": "template",
                        "company": owner,
                        "url": readme_url,
                        "text": rr.text[:80000],
                        "word_count": len(rr.text.split()),
                        "license": repo.get("license", {}).get("spdx_id", "unknown"),
                    }
                    (OUTPUT / f"github_{record['contract_id']}.json").write_text(
                        json.dumps(record, indent=2)
                    )
                    collected += 1
                time.sleep(1)
            except Exception:
                pass
    except Exception as e:
        print(f"  GitHub search error: {e}")

    print(f"  GitHub: {collected}")
    return collected


def main():
    print("=== Creative Commons Scraper === target=2,000\n")

    d = scrape_docracy(target=800)
    o = scrape_onecle(target=700)
    g = scrape_github(target=500)

    total = d + o + g
    print(f"\n✅ Creative Commons total: {total} contracts saved to {OUTPUT}/")


if __name__ == "__main__":
    main()
