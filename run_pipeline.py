import os
import sys
from datetime import datetime, UTC
import json
from icp.gate import ICPGate

PROJECT_ROOT = "/content/drive/MyDrive/clickpost-intent-engine"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -----------------------------------------
# Project Imports
# -----------------------------------------

from openai import OpenAI
from google.colab import userdata

from config import BRANDS
from fetch.fetch_pages import fetch_page
from fetch.fetch_reddit import fetch_reddit_posts
from fetch.utils import (
    save_text,
    save_json,
    find_first_working_page,
)

from extract.extractor import SignalExtractor
from verify.verifier import SignalVerifier
from verify.rule_filter import filter_signals
from score.scorer import IntentScorer
from outreach.generator import OutreachGenerator
from icp.gate import ICPGate

# -----------------------------------------
# OpenAI Client
# -----------------------------------------

api_key = None

# Try Colab Secrets
try:
    api_key = userdata.get("OPENAI_API_KEY")
except Exception:
    pass

# Fall back to environment
if not api_key:
    api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    api_key = api_key.strip()


if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found.")

client = OpenAI(api_key=api_key)

# -----------------------------------------
# Pipeline Components
# -----------------------------------------

extractor = SignalExtractor(client)
verifier = SignalVerifier()
scorer = IntentScorer()
outreach = OutreachGenerator(client)
icp_gate = ICPGate()

# -----------------------------------------
# Configuration
# -----------------------------------------

RETURN_PATHS = [
    "/pages/returns",
    "/pages/return-policy",
    "/returns",
    "/return-policy",
]

CAREER_PATHS = [
    "/pages/careers",
    "/careers",
    "/jobs",
]

REDDIT_SOURCE_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "sources",
    "reddit_urls.json",
)

PAGE_SOURCE_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "sources",
    "page_urls.json",
)

# -----------------------------------------
# Load curated page URLs
# -----------------------------------------

print("\n" + "="*60)
print("LOADING PAGE_URLS")
print("="*60)

PAGE_URLS = {}

if os.path.exists(PAGE_SOURCE_FILE):
    with open(PAGE_SOURCE_FILE, "r", encoding="utf-8") as f:
        PAGE_URLS = json.load(f)else:
# -----------------------------------------
# Debug: Print BRANDS and PAGE_URLS
# -----------------------------------------

print("\n" + "="*60)
print("="*60)
for b in BRANDS:
print("\n" + "="*60)
print("="*60)
for k in PAGE_URLS.keys():print("="*60 + "\n")

# -----------------------------------------
# Pipeline
# -----------------------------------------

for brand in BRANDS:

    brand_name = brand["name"]
    website = brand["website"]

    # -----------------------------------------
    # Debug: Check if brand is in PAGE_URLS
    # -----------------------------------------
    print("\n" + "="*60)    
    if brand_name in PAGE_URLS:    else:        for k in PAGE_URLS.keys():
            # Check if first word matches
            brand_first_word = brand_name.lower().split()[0] if brand_name.lower().split() else ""
            k_first_word = k.lower().split()[0] if k.lower().split() else ""
            if brand_first_word in k.lower() or k_first_word in brand_name.lower():    print("="*60 + "\n")

    print("=" * 60)
    print(f"Processing {brand_name}")
    print("=" * 60)

    raw_dir = os.path.join(PROJECT_ROOT, "data", "raw", brand_name)
    extracted_dir = os.path.join(PROJECT_ROOT, "data", "extracted", brand_name)
    verified_dir = os.path.join(PROJECT_ROOT, "data", "verified", brand_name)
    scored_dir = os.path.join(PROJECT_ROOT, "data", "scored", brand_name)
    outreach_dir = os.path.join(PROJECT_ROOT, "data", "outreach", brand_name)

    for folder in [
        raw_dir,
        extracted_dir,
        verified_dir,
        scored_dir,
        outreach_dir,
    ]:
        os.makedirs(folder, exist_ok=True)

    metadata = {
        "brand": brand_name,
        "website": website,
        "fetched_at": datetime.now(UTC).isoformat(),
        "sources": [],
    }

    # -----------------------------------------
    # Fetch Returns & Careers Pages
    # -----------------------------------------

    for page_type in ["returns", "careers"]:

        result = None

        # ---------- First try curated URL ----------        if brand_name in PAGE_URLS:        
        if (
            brand_name in PAGE_URLS
            and PAGE_URLS[brand_name].get(page_type)
        ):

            curated_url = PAGE_URLS[brand_name][page_type]
            result = fetch_page(
                curated_url,
                page_type=page_type,
            )

            # Debug: Check if fetch actually succeeded
            print(
                f"{brand_name} {page_type}:",
                result["success"],
                result["status_code"],
                result["error"],
            )

            # Only keep result if fetch succeeded
            if result["success"]:
                result["url"] = curated_url
            else:
                result = None

        # ---------- Fallback to URL guessing ----------
        if result is None:            
            candidate_paths = (
                RETURN_PATHS
                if page_type == "returns"
                else CAREER_PATHS
            )

            result = find_first_working_page(
                website,
                candidate_paths,
                lambda url: fetch_page(
                    url,
                    page_type=page_type,
                ),
            )

        # Record metadata with correct success status
        if result and result.get("success"):
            success = True
            status_code = result.get("status_code")
            error = None
            url = result.get("url")
        else:
            success = False
            status_code = result.get("status_code") if result else None
            error = result.get("error") if result else f"No {page_type} page found"
            url = result.get("url") if result else None

        metadata["sources"].append(
            {
                "type": page_type,
                "url": url,
                "status_code": status_code,
                "success": success,
                "error": error,
            }
        )

        if result and result.get("success"):

            save_text(
                os.path.join(
                    raw_dir,
                    f"{page_type}.txt",
                ),
                result["text"],
            )

            print(f"✓ {page_type.capitalize()} page saved")

        else:

            print(f"✗ {page_type.capitalize()} page not found")

    # -----------------------------------------
    # Fetch Reddit
    # -----------------------------------------

    posts, failures = fetch_reddit_posts(
        brand_name,
        REDDIT_SOURCE_FILE,
    )

    save_json(
        os.path.join(raw_dir, "reddit.json"),
        posts,
    )

    save_json(
        os.path.join(
            raw_dir,
            "reddit_fetch_errors.json",
        ),
        failures,
    )

    metadata["sources"].append(
        {
            "type": "reddit",
            "configured_urls": len(posts) + len(failures),
            "successful_fetches": len(posts),
            "failed_fetches": len(failures),
        }
    )

    print(
        f"✓ Reddit: {len(posts)} fetched, {len(failures)} failed"
    )

    # -----------------------------------------
    # Load fetched text
    # -----------------------------------------

    returns_text = ""
    careers_text = ""

    returns_file = os.path.join(raw_dir, "returns.txt")
    careers_file = os.path.join(raw_dir, "careers.txt")

    if os.path.exists(returns_file):
        with open(returns_file, "r", encoding="utf-8") as f:
            returns_text = f.read()

    if os.path.exists(careers_file):
        with open(careers_file, "r", encoding="utf-8") as f:
            careers_text = f.read()

    # -----------------------------------------
    # Extract
    # -----------------------------------------

    if returns_text:
        returns_extract = extractor.extract(
            brand_name,
            returns_text,
            "returns",
        )
        # Apply rule-based filtering to prevent model drift
        returns_extract["signals"] = filter_signals(
            returns_extract["signals"]
        )
    else:
        returns_extract = {
            "brand": brand_name,
            "signals": [],
            "error": None,
        }

    save_json(
        os.path.join(extracted_dir, "returns.json"),
        returns_extract,
    )

    if careers_text:
        careers_extract = extractor.extract(
            brand_name,
            careers_text,
            "careers",
        )
        # Apply rule-based filtering to prevent model drift
        careers_extract["signals"] = filter_signals(
            careers_extract["signals"]
        )
    else:
        careers_extract = {
            "brand": brand_name,
            "signals": [],
            "error": None,
        }

    save_json(
        os.path.join(extracted_dir, "careers.json"),
        careers_extract,
    )

    # -----------------------------------------
    # Verify
    # -----------------------------------------

    if (
        returns_text
        and returns_extract.get("signals")
        and not returns_extract.get("error")
    ):
        returns_verified = verifier.verify(
            returns_extract,
            returns_text,
        )
    else:
        returns_verified = {
            "brand": brand_name,
            "signals": returns_extract.get("signals", []),
            "error": returns_extract.get("error"),
        }

    save_json(
        os.path.join(verified_dir, "returns.json"),
        returns_verified,
    )

    if (
        careers_text
        and careers_extract.get("signals")
        and not careers_extract.get("error")
    ):
        careers_verified = verifier.verify(
            careers_extract,
            careers_text,
        )
    else:
        careers_verified = {
            "brand": brand_name,
            "signals": careers_extract.get("signals", []),
            "error": careers_extract.get("error"),
        }

    save_json(
        os.path.join(verified_dir, "careers.json"),
        careers_verified,
    )

    # -----------------------------------------
    # Merge
    # -----------------------------------------

    merged_error = (
        returns_verified.get("error")
        or careers_verified.get("error")
    )

    merged = {
        "brand": brand_name,
        "signals": (
            returns_verified.get("signals", [])
            + careers_verified.get("signals", [])
        ),
        "error": merged_error,
    }

            
        
            
    # -----------------------------------------
    # Score
    # -----------------------------------------

    # Determine fetch status
    returns_meta = next(
        (s for s in metadata["sources"] if s["type"] == "returns"),
        None,
    )

    careers_meta = next(
        (s for s in metadata["sources"] if s["type"] == "careers"),
        None,
    )

    returns_success = (
        returns_meta is not None
        and returns_meta.get("success", False)
    )

    careers_success = (
        careers_meta is not None
        and careers_meta.get("success", False)
    )

    # -------------------------------------------------
    # Build error message for failed fetches
    # -------------------------------------------------

    fetch_errors = []

    if not returns_success:
        if returns_meta and returns_meta.get("error"):
            fetch_errors.append(
                f"Returns page: {returns_meta['error']}"
            )
        else:
            fetch_errors.append("Returns page not found")

    if not careers_success:
        if careers_meta and careers_meta.get("error"):
            fetch_errors.append(
                f"Careers page: {careers_meta['error']}"
            )
        else:
            fetch_errors.append("Careers page not found")

    # -------------------------------------------------
    # Score
    # -------------------------------------------------

    if merged.get("error"):

        score_result = {
            "brand": brand_name,
            "score": None,
            "signals": merged["signals"],
            "error": merged["error"],
            "data_status": "EXTRACTION_FAILED",
        }

    elif not returns_success and not careers_success:

        # Neither source could be fetched

        score_result = {
            "brand": brand_name,
            "score": 0,
            "signals": [],
            "error": " | ".join(fetch_errors),
            "data_status": "INCOMPLETE",
        }

    elif merged["signals"]:

        score_result = scorer.score(merged)
        score_result["data_status"] = "COMPLETE"

    else:

        # Pages fetched successfully but no intent signals

        score_result = {
            "brand": brand_name,
            "score": 0,
            "signals": [],
            "error": None,
            "data_status": "COMPLETE",
        }

    # -----------------------------------------
    # ICP Gate
    # -----------------------------------------

    score_result["icp"] = icp_gate.evaluate(
        score_result["brand"]
    )

    save_json(
        os.path.join(scored_dir, "intent_score.json"),
        score_result,
    )

    print(
        f"✓ Intent Score: {score_result['score']}"
    )
    print(
        f"✓ ICP Eligible: {score_result['icp']['eligible']}"
    )

    # -----------------------------------------
    # Outreach - Only generate for ICP-eligible brands with positive scores
    # -----------------------------------------

    if (
        score_result["score"] is not None
        and score_result["score"] > 0
        and score_result["icp"]["eligible"]
    ):

        outreach_result = outreach.generate(
            score_result
        )

    else:
        # Determine why outreach was skipped
        if score_result["score"] is None:
            error = "EXTRACTION_FAILED"
        elif score_result["score"] <= 0:
            error = "LOW_SCORE"
        elif not score_result["icp"]["eligible"]:
            error = "NOT_ICP_ELIGIBLE"
        else:
            error = "UNKNOWN_REASON"
            
        outreach_result = {
            "email": None,
            "linkedin": None,
            "error": error,
        }

    save_json(
        os.path.join(
            outreach_dir,
            "outreach.json",
        ),
        outreach_result,
    )

    if outreach_result["email"]:
        print("✓ Outreach generated")
    else:
        print(f"✗ No outreach generated ({outreach_result.get('error', 'UNKNOWN')})")

    # -----------------------------------------
    # Save Metadata
    # -----------------------------------------

    save_json(
        os.path.join(
            raw_dir,
            "metadata.json",
        ),
        metadata,
    )

print("\nDone!")