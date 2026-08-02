# ClickPost Intent-Based Account Prioritization Engine

An end-to-end AI-powered pipeline that identifies and ranks Direct-to-Consumer (DTC) brands based on publicly observable logistics intent signals.

Instead of ranking accounts by company size or generic firmographic data, this project discovers operational buying intent from publicly available sources such as returns policies and careers pages, verifies extracted evidence against the original webpages, scores intent using a deterministic taxonomy, applies an Ideal Customer Profile (ICP) gate, and generates personalized outbound outreach.

---

# Features

- Automated webpage fetching
- ATS (Greenhouse / Lever / BuiltIn) career page discovery
- GPT-based logistics signal extraction
- Deterministic false-positive filtering
- Exact evidence verification against source documents
- Intent scoring using weighted operational taxonomy
- ICP eligibility gate
- Account ranking
- Personalized outreach generation
- Intermediate artifacts saved for complete auditability

---

# System Architecture

```
                    Curated URLs
                         │
                         ▼
                Page Fetching
          (Returns + Careers Pages)
                         │
                         ▼
              GPT Signal Extraction
                         │
                         ▼
         Deterministic Rule Filtering
                         │
                         ▼
            Evidence Verification
                         │
                         ▼
               Intent Scoring
                         │
                         ▼
               ICP Eligibility Gate
                         │
                         ▼
                Account Ranking
                         │
                         ▼
          Personalized Outreach
```

---

# Project Structure

```
clickpost-intent-engine/

│
├── fetch/
│   ├── fetch_pages.py
│   ├── fetch_reddit.py
│   └── utils.py
│
├── extract/
│   ├── extractor.py
│   ├── prompts.py
│   └── client.py
│
├── verify/
│   ├── verifier.py
│   └── rule_filter.py
│
├── score/
│   └── scorer.py
│
├── icp/
│   └── gate.py
│
├── ranking/
│   └── ranker.py
│
├── outreach/
│   ├── generator.py
│   └── prompts.py
│
├── data/
│   ├── raw/
│   ├── extracted/
│   ├── verified/
│   ├── scored/
│   ├── outreach/
│   └── final/
│
├── config.py
├── run_pipeline.py
├── requirements.txt
├── memo.md
└── README.md
```

---

# Pipeline

## 1. Fetch

For every target brand the system attempts to retrieve:

- Returns / Shipping Policy
- Careers Page

If curated URLs are unavailable, common URL patterns are attempted automatically.

ATS-hosted career pages are automatically followed where supported.

---

## 2. Signal Extraction

GPT extracts structured operational signals including:

- Shipping issues
- Delivery issues
- Returns issues
- Reverse logistics
- Logistics hiring
- Customer support hiring
- Warehouse expansion
- Carrier partnerships

Each extracted signal contains:

- signal type
- evidence
- source
- originating brand

---

## 3. Rule-Based Filtering

A deterministic filtering layer removes common false positives such as:

- Generic careers headings
- "Open Roles"
- Positive marketing language
- Routine return policy text
- Generic refund instructions
- Boilerplate FAQ content

This reduces hallucinated logistics signals before verification.

---

## 4. Evidence Verification

Every extracted evidence sentence is verified using exact substring matching against the original fetched document.

Signals are marked as:

- verified
- manual_review

Only verified evidence contributes to intent scoring.

---

## 5. Intent Scoring

Each operational signal category contributes a predefined weight.

| Signal | Weight |
|---------|--------|
| Warehouse Expansion | 9 |
| Carrier Partnership | 9 |
| Shipping Issue | 8 |
| Delivery Issue | 8 |
| Returns Issue | 7 |
| Reverse Logistics | 7 |
| Hiring Logistics | 6 |
| Hiring Customer Support | 5 |

Scores are calculated **once per unique signal category**, preventing repeated FAQ statements from artificially inflating rankings while preserving all supporting evidence.

---

## 6. ICP Gate

Each company is evaluated against three manually curated criteria:

- Direct-to-Consumer
- Mid-market
- Physical products

Brands remain in the ranking even if they require manual review.

Example:

```
Eligible: True

Flagged for Review: True

Reason:
Public research indicates unicorn-scale valuation and business scale that may exceed the target ICP.
```

---

## 7. Ranking

Accounts are ranked using:

- verified operational signals
- deterministic weights
- ICP eligibility

Incomplete fetches are explicitly labeled rather than treated as successfully evaluated.

---

## 8. Outreach Generation

Personalized outreach is generated only for accounts containing verified operational signals.

Brands with no verified signals do not receive generated outreach.

---

# Validation

The pipeline was validated through:

- repeated deterministic runs on identical inputs
- manual comparison of verified evidence against raw fetched webpages
- inspection of intermediate artifacts
- iterative reduction of false positives discovered during development

---

# Example Output

```
Rank    Brand                 Score

1       Native Deodorant        21
2       Tushy                   20
3       Beardbrand              15
4       Momofuku Goods          15
5       Graza                   13
6       Caraway                 13
7       Olipop                  13
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/gotnochill815-web/clickpost-intent-engine.git

cd clickpost-intent-engine
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=YOUR_API_KEY
```

or in Google Colab:

```python
from google.colab import userdata
import os

os.environ["OPENAI_API_KEY"] = userdata.get("OPENAI_API_KEY")
```

---

# Running

```bash
python run_pipeline.py
```

Outputs are written to:

```
data/raw/

data/extracted/

data/verified/

data/scored/

data/outreach/

data/final/
```

---

# Technologies

- Python
- OpenAI GPT
- BeautifulSoup
- Requests
- Pandas
- lxml
- dotenv

---

# Limitations

- Public webpages only
- Some websites block automated fetching (403, SSL)
- FAQ-style pages may still produce false-positive operational signals despite deterministic filtering
- ICP labels are manually curated
- Website content changes over time and may affect extracted evidence

---

# Future Improvements

- Retrieval-Augmented Generation (RAG)
- Semantic evidence deduplication
- Automatic ICP inference
- News and earnings integration
- Confidence calibration
- Human feedback loop
- Interactive web application

---

# Author

**Prakhya Khandelwal**

AI/ML Engineer | Applied LLMs | Information Retrieval | Intelligent Automation

GitHub:
https://github.com/gotnochill815-web

---

# License

This project was developed as part of a technical assessment for ClickPost and is intended for educational and portfolio purposes.
