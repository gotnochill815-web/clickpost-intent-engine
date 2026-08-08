#  Intent-Based Account Prioritization Engine

An end-to-end AI-powered pipeline that identifies, verifies, ranks, and activates Direct-to-Consumer (D2C) brands based on publicly observable buying-intent signals.

Instead of relying on firmographic attributes or company size alone, this project discovers operational buying intent from publicly available sources such as returns policies and careers pages, verifies every extracted signal against its original webpage, scores accounts using an explainable rule-based taxonomy, applies an Ideal Customer Profile (ICP) gate, and generates personalized outbound outreach grounded only in verified evidence.

---

# Overview

The pipeline answers a practical sales question:

> **Which D2C brands are most likely to benefit from ClickPost today, and why?**

Rather than treating every company equally, the system searches for operational evidence that may indicate logistics or post-purchase challenges and converts those observations into explainable buying-intent scores.

---

# Features

- Automated webpage fetching
- ATS (Greenhouse, Lever, SmartRecruiters, BuiltIn) career page discovery
- GPT-powered operational signal extraction
- Deterministic false-positive filtering
- Exact evidence verification against original webpages
- Explainable rule-based intent scoring
- ICP eligibility evaluation
- Account ranking
- Grounded outbound generation (Email + LinkedIn)
- CSV and JSON output generation
- Intermediate artifacts saved for complete auditability

---

# System Architecture

```
                 Curated Brand URLs
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
      Grounded Outreach Generation
```

---

# Project Structure

```
intent-engine/

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

For every target brand, the pipeline retrieves:

- Returns / Shipping Policy
- Careers Page

If careers pages redirect to ATS platforms (Greenhouse, Lever, SmartRecruiters, BuiltIn), the crawler automatically follows the redirect.

---

## 2. Signal Extraction

GPT extracts candidate operational signals directly from webpage content.

The final scoring pipeline focuses on four signal categories:

- Hiring Logistics
- Hiring Customer Support
- Returns Issues
- Reverse Logistics

Each extracted signal contains:

- signal type
- evidence
- source
- originating brand

---

## 3. Rule-Based Filtering

A deterministic filtering layer removes common false positives before verification.

Examples include:

- Generic careers headings
- "Apply Now"
- "Open Roles"
- FAQ headings
- Routine return-policy language
- Boilerplate legal text
- Generic customer-support instructions

This reduces hallucinated or low-quality operational signals.

---

## 4. Evidence Verification

Every extracted evidence quote is verified using exact substring matching against the original fetched webpage.

Signals are labeled as:

- **verified**
- **manual_review**

Only verified signals contribute to intent scoring.

---

## 5. Intent Scoring

Intent is scored using an explainable weighted taxonomy.

| Signal | Weight |
|---------|--------|
| Returns Issue | 7 |
| Reverse Logistics | 7 |
| Hiring Logistics | 6 |
| Hiring Customer Support | 5 |

Each signal category contributes only once per account, preventing repeated FAQ statements from artificially inflating scores while preserving all supporting evidence.

---

## 6. ICP Gate

Each company is evaluated using three manually curated criteria:

- Direct-to-Consumer
- Mid-market
- Physical products

Companies remain in the ranked output even when flagged for manual review.

Example:

```
Eligible: True

Flagged for Review: True

Reason:
Public information suggests the company may exceed the intended ICP size.
```

---

## 7. Ranking

Accounts are ranked using:

- verified operational signals
- deterministic scoring
- ICP eligibility

Brands with incomplete webpage retrieval are explicitly identified rather than silently treated as successful evaluations.

---

## 8. Grounded Outreach Generation

Personalized outreach is generated only for accounts containing verified operational signals.

The generator:

- references only verified evidence
- avoids unsupported business assumptions
- produces:
  - personalized cold email
  - LinkedIn connection request

This ensures every outreach message remains grounded in publicly verifiable information.

---

# Validation

The pipeline was iteratively validated through:

- repeated pipeline executions
- manual verification against source webpages
- inspection of intermediate artifacts
- deterministic filtering
- comparison of extracted evidence with original webpages

During development, several scoring and filtering regressions were identified and used to improve the final pipeline.

---

# Example Results

The final evaluation produced the following ranked accounts:

| Rank | Brand | Score |
|------|--------|------:|
| 1 | Graza | 13 |
| 2 | Blueland | 11 |
| 3 | Rothy's | 7 |
| 4 | Vuori | 5 |
| 5 | Caraway | 5 |
| 6 | Jones Road Beauty | 5 |
| 7 | Brooklinen | 0 |
| 8 | Solo Stove | 0 |
| 9 | Kosas | 0 |
|10 | Liquid Death | 0 |
|11 | Our Place | 0 |
|12 | Magic Spoon | 0 |

Grounded outbound sequences were automatically generated for accounts with verified buying-intent signals.

---

# Installation

Clone the repository:

```bash
git clone https://github.com/gotnochill815-web/intent-engine.git

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

Execute:

```bash
python run_pipeline.py
```

Generated outputs include:

```
data/raw/

data/extracted/

data/verified/

data/scored/

data/outreach/

data/final/

ranked_accounts.csv

ranked_accounts.json
```

---

# Technologies

- Python
- OpenAI GPT
- BeautifulSoup
- Requests
- Pandas
- lxml
- python-dotenv

---

# Design Decisions

Several alternative approaches were explored during development, including extracting signals from About pages, Press releases, Blogs, and Reddit.

While these sources occasionally surfaced interesting company updates, they also introduced significantly more false positives and weaker buying-intent evidence.

The final pipeline therefore prioritizes Returns and Careers pages, as these consistently produced the most reliable operational signals for ClickPost's use case.

---

# Limitations

- Uses only publicly available webpages
- Some websites block automated scraping (HTTP 403, SSL issues)
- Signal weights are heuristic rather than learned from historical CRM outcomes
- ICP labels are manually curated
- Website content changes over time and may affect extracted evidence
- LLM extraction still requires deterministic verification to reduce false positives

---

# Future Improvements

- Retrieval-Augmented Generation (RAG) over company documentation
- Automated regression testing using a gold-standard evaluation dataset
- CRM feedback loop for learning signal weights
- Automatic ICP inference
- Continuous monitoring of buying-intent signals
- Interactive dashboard for SDR workflows

---

# Author

**Prakhya Khandelwal**

AI/ML Engineer | Applied LLMs | Information Retrieval | Intelligent Automation

GitHub:
https://github.com/gotnochill815-web

Google Colab:
https://colab.research.google.com/drive/18pcBM1uG5t35RWpY8OJJoiwyrUl9P09d

---

# License

This project was developed as part of the **ClickPost AI Engineer Internship Technical Assessment** and is intended for educational and portfolio purposes.
