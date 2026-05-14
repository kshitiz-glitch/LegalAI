"""
Dataset 1b: SEC EDGAR 8-K filings — target 5,000 contracts
Covers: M&A, partnership, licensing, credit, supply, distribution agreements
Output: data/raw/sec_edgar/<ticker>_<id>.json

100% legal — public government data designed for bulk download.
"""
import json
import re
import uuid
from pathlib import Path

OUTPUT = Path("data/raw/sec_edgar")
OUTPUT.mkdir(parents=True, exist_ok=True)

EDGAR_DOWNLOAD_DIR = Path("data/raw/edgar_downloads")

# Fortune 500 + diverse sector coverage
TICKERS = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "ADBE", "CRM", "INTC",
    "ORCL", "IBM", "CSCO", "QCOM", "TXN", "AMD", "SHOP", "NOW", "SNOW", "PLTR",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP", "V", "MA",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "BMY", "AMGN", "GILD", "CVS", "CI",
    # Consumer / Retail
    "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "COST", "PG", "KO", "PEP",
    # Energy / Industrial
    "XOM", "CVX", "GE", "HON", "CAT", "BA", "LMT", "RTX", "DE", "MMM",
    # Media / Telecom
    "DIS", "NFLX", "CMCSA", "T", "VZ",
]

MIN_TEXT_LEN = 500
MAX_TEXT_LEN = 100_000

CONTRACT_KEYWORDS = [
    "agreement", "contract", "parties agree", "whereas", "now therefore",
    "in consideration", "termination", "governing law",
]


def is_contract_text(text: str) -> bool:
    t = text.lower()
    return sum(1 for kw in CONTRACT_KEYWORDS if kw in t) >= 3


def clean_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_contracts_from_filing(filing_path: Path) -> list[str]:
    contracts = []
    content = filing_path.read_text(errors="ignore")

    # Split by exhibit separator
    exhibits = re.split(r"<DOCUMENT>|</DOCUMENT>", content)

    for exhibit in exhibits:
        if "<TYPE>EX-" not in exhibit and "EXHIBIT" not in exhibit.upper():
            continue

        text = clean_html(exhibit)

        if MIN_TEXT_LEN <= len(text) <= MAX_TEXT_LEN and is_contract_text(text):
            contracts.append(text)

    return contracts


def main():
    try:
        from sec_edgar_downloader import Downloader
    except ImportError:
        print("Install: pip install sec-edgar-downloader")
        return

    dl = Downloader("LegalAI-Research", "legal@legalai.com", EDGAR_DOWNLOAD_DIR)

    total = 0
    target = 5000

    print(f"=== SEC EDGAR Scraper === target={target}")

    for ticker in TICKERS:
        if total >= target:
            break
        try:
            print(f"\n[{ticker}] Downloading 8-K filings…")
            dl.get("8-K", ticker, after="2020-01-01", before="2024-12-31", limit=15)

            filing_dir = EDGAR_DOWNLOAD_DIR / "sec-edgar-filings" / ticker / "8-K"
            if not filing_dir.exists():
                continue

            for filing_folder in filing_dir.iterdir():
                if total >= target:
                    break
                for f in filing_folder.glob("*.txt"):
                    contracts = extract_contracts_from_filing(f)
                    for text in contracts:
                        if total >= target:
                            break

                        contract_id = str(uuid.uuid4())[:8]
                        record = {
                            "contract_id": contract_id,
                            "source": "sec_edgar",
                            "contract_type": "public_company_filing",
                            "company": ticker,
                            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=8-K",
                            "text": text[:MAX_TEXT_LEN],
                            "word_count": len(text.split()),
                        }

                        out_file = OUTPUT / f"{ticker}_{contract_id}.json"
                        out_file.write_text(json.dumps(record, indent=2))
                        total += 1

            print(f"  Running total: {total}")

        except Exception as e:
            print(f"  [{ticker}] error: {e}")

    print(f"\n✅ SEC EDGAR: {total} contracts saved to {OUTPUT}/")


if __name__ == "__main__":
    main()
