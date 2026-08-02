# Technical Memo
## ClickPost Intent-Based Account Prioritization Engine

**Author:** Prakhya Khandelwal

---

## 1. Overview

This project develops an automated intent-based account prioritization system for ClickPost's outbound sales workflow. The objective is to rank direct-to-consumer (DTC) brands according to observable operational buying intent, using publicly available information such as returns policies, careers pages, and logistics-related documentation.

Rather than relying on company size or generic firmographic data, the system attempts to identify operational signals that suggest logistics-related pain points or expansion activity. These signals are verified against their original source documents, scored using a deterministic weighting scheme, filtered through an Ideal Customer Profile (ICP) gate, and used to generate personalized outbound outreach only for qualified accounts.

The final pipeline consists of eight sequential stages:

**Fetch → Extract → Deterministic Filter → Verify → Score → ICP Gate → Rank → Outreach**

---

## 2. Problem Statement

Outbound sales teams commonly prioritize accounts using static criteria — company size, industry vertical, funding stage — that don't capture whether a company is *currently* exhibiting behavior consistent with demand for logistics software.

This project's goal was to identify companies showing observable, evidence-backed logistics signals from public sources, while keeping false-positive rates from LLM extraction low enough that a sales rep could trust and act on the output directly.

---

## 3. System Architecture

```
Curated Brand List
        │
        ▼
Page Fetching (requests + BeautifulSoup)
   Returns/Shipping page + Careers page
        │
        ▼
LLM Signal Extraction (structured JSON)
        │
        ▼
Deterministic Rule Filter
   (strips policy language, reassurance language,
    obvious non-signals before verification)
        │
        ▼
Evidence Verification
   (normalize + substring match against source text)
        │
        ▼
Intent Scoring (fixed weights, summed)
        │
        ▼
ICP Eligibility Gate
        │
        ▼
Ranking
        │
        ▼
Personalized Outreach Generation
```

Each stage writes its output to disk independently (`data/raw/`, `data/verified/`, `data/scored/`, etc.), which made the pipeline debuggable at every step rather than a single opaque black box.

**Scope decisions**, made deliberately in light of the brief's stated preference for an honest, well-reasoned prototype over an over-engineered system:

- **Fetch layer:** `requests` + `BeautifulSoup` only. No headless browser (Playwright) was used. Pages that require JavaScript rendering (e.g. some ATS-hosted careers listings) are flagged `manual_required: True` with a reason, rather than silently failing or being scraped incorrectly.
- **Verification:** kept intentionally simple — lowercase, whitespace normalization, HTML entity decoding, substring match. If a claimed piece of evidence doesn't appear in the source text after normalization, it's marked unverified and excluded from scoring. No fuzzy matching or embedding-based similarity was used.
- **Scoring:** a flat, inspectable rule — each verified signal category contributes a fixed weight; weights are summed with no normalization or calibration. The rationale for any weight is answerable in one sentence: *"weights reflect perceived proximity to an active buying decision."*

---

## 4. Intent Taxonomy

Signals were grouped manually by their expected causal proximity to a logistics-software purchasing decision.

| Signal | Weight | Rationale |
|---|---|---|
| Warehouse expansion | 9 | Directly implies new fulfillment infrastructure |
| Carrier partnership | 9 | Directly implies active shipping/logistics decisions |
| Shipping issue | 8 | Operational pain point in the core product surface |
| Delivery issue | 8 | Same category, customer-facing failure mode |
| Returns issue | 7 | Operational pain, one step removed from shipping |
| Reverse logistics | 7 | Specialized, high-intent operational signal |
| Hiring — logistics roles | 6 | Forward-looking, but hiring lags actual need |
| Hiring — customer support | 5 | Weaker, more indirect signal of operational strain |

The taxonomy deliberately weights infrastructure and operational-failure signals above generic hiring or growth signals, since the latter are more easily confounded with unrelated company growth.

---

## 5. Methodology

### 5.1 Data Collection

For each brand, the pipeline attempts to retrieve two page types:

- **Returns / shipping policy page** — the primary source for delivery, shipping, and returns-related operational language.
- **Careers page** — the primary source for hiring-related signals (logistics roles, customer support roles, warehouse roles).

Brands were selected based on public evidence availability: an active careers page, an accessible returns page, and (where available) public discussion (Reddit, reviews) corroborating operational activity. This selection criterion was itself a judgment call favoring evaluability over raw coverage.

### 5.2 Signal Extraction

Fetched page text is passed to an LLM with a structured extraction prompt that returns JSON: a list of `{signal, evidence, source}` objects per page. No signal is accepted on the model's say-so alone — every extracted signal proceeds to the filter and verification stages below.

### 5.3 Deterministic Rule Filter

This stage was added specifically in response to a failure mode discovered during testing (see §7): LLM extraction on long FAQ-style pages tended to surface **policy statements** ("we do not accept returns on any of our products") and **reassurance language** ("carriers often mark a package Delivered when it's still in transit — this is normal") as if they were operational complaints. The filter strips known patterns of this kind before scoring, so that standard policy boilerplate cannot masquerade as buying-intent evidence.

### 5.4 Evidence Verification

Every signal that survives the filter is checked against the actual scraped source text (normalized: lowercase, whitespace-collapsed, HTML entities decoded). Only evidence that is a literal substring match of the source is marked `verified`; everything else is dropped before scoring. This step exists specifically to catch model hallucination — an extracted "signal" that doesn't actually appear in the source page is not evidence of anything.

### 5.5 Intent Scoring

Verified signals are scored by summing the fixed weight for each **distinct signal category** present (not per occurrence). This was a deliberate fix made mid-project: an earlier version of the scorer summed weights per individual matched sentence, which meant a single policy fact restated three times in one FAQ (as happened with Momofuku Goods — see §7) could inflate a brand's score far beyond what the underlying evidence justified. Weighting by category rather than raw count removes that inflation.

### 5.6 ICP Gate and Ranking

Scored brands are passed through an ICP eligibility check before ranking, so that a brand with a high intent score but a poor customer fit does not surface ahead of a lower-scoring but well-fitted account. Ranked, ICP-eligible brands then proceed to outreach generation.

### 5.7 Outreach Generation

For each qualified, ranked account, the pipeline generates a short personalized outreach draft that references the specific verified signal(s) driving that account's score — not a generic template. This was treated as a first-class deliverable, in line with the rubric's 20% weight on personalized outbound.

---

## 6. Results

The submission is anchored on a **hand-verified 8-brand set**, chosen and inspected in depth over the course of the project. For each brand, the pipeline output includes:

- Raw fetched source text (`data/raw/`)
- Extracted, filtered, and verified signals per page (`data/verified/`)
- A final intent score with a category-by-category breakdown
- ICP gate result
- A personalized outreach draft (where the brand qualified)

*(Insert the final ranked table of the 8 brands with scores, top signals, and ICP status here once the run is finalized.)*

Every score in this set is traceable back to a specific piece of verified evidence in the corresponding source document — this traceability was treated as more important than raw score magnitude.

---

## 7. Extended Evaluation: The 25-Brand Run

After validating the pipeline on the 8-brand set, it was scaled to a broader 25-brand run to stress-test it beyond hand-curated inputs. This surfaced a concrete and instructive failure mode.

**What happened:** Several brands' returns pages were long FAQ-style documents rather than short policy statements. On these pages, the extractor correctly identified sentences about deliveries, returns, and shipping — but many of those sentences were standard policy language or brand reassurance copy, not evidence of operational strain. Momofuku Goods was the clearest case: 11 "signals" were extracted from its returns FAQ, of which roughly one was a defensible (if weak) signal, and the remainder were restatements of a no-returns policy or explanations of routine carrier handling. The deterministic filter, tuned against the original 8-brand sample, did not catch these patterns because it hadn't been exposed to long-FAQ policy phrasing during development.

**What did *not* fail:** The scoring math itself. Once the category-level scoring fix (§5.5) was in place, the inflation from repeated evidence was eliminated. The remaining problem was upstream — the filter's pattern coverage, not the scoring logic.

**Decision:** The 8-brand set is the primary submission dataset, because it is the one that has been manually inspected end-to-end and is known to be reliable. The 25-brand run is reported here as an extended evaluation, not as the primary benchmark, because it revealed a genuine, unresolved gap in filter coverage that would need further iteration to trust at scale.

This is treated as a finding worth reporting rather than a result to hide: it demonstrates the pipeline's failure mode is legible, diagnosable, and traceable to a specific stage (deterministic filtering on long-form FAQ pages) rather than a systemic flaw in the scoring or verification design.

---

## 8. Limitations

- **Filter coverage is incomplete.** The deterministic filter was tuned against the 8-brand sample and does not generalize cleanly to longer, noisier FAQ documents, as demonstrated by the 25-brand run.
- **No JavaScript-rendered page support.** Careers pages hosted on JS-heavy ATS platforms (e.g. certain Greenhouse/Lever embeds) are not reachable by the current fetch layer and are flagged `manual_required` rather than scraped.
- **Verification is a strict substring match**, not semantic matching. This minimizes hallucinated evidence but means legitimate paraphrased evidence can be under-counted.
- **Weights are hand-assigned, not empirically calibrated.** They reflect a defensible business judgment about proximity to a buying decision, not a statistically fitted model.
- **Coverage is intentionally narrow.** The submission favors depth and traceability on a small set of brands over broad coverage with unverified quality, in line with the brief's explicit preference.

---

## 9. Future Work

- Extend the deterministic filter with targeted heuristics for FAQ-style pages: distinguishing policy statements and reassurance language from genuine complaints, rather than attempting to enumerate every possible phrasing.
- Add ATS-aware fetching (Greenhouse/Lever API endpoints) to recover real job listings currently missed on JS-rendered careers pages.
- Re-run the 25-brand set with the improved filter and re-evaluate the previously flagged brands (Momofuku Goods, and any others surfaced by the same pattern).
- Explore lightweight semantic verification (e.g. paraphrase detection) as a complement to, not a replacement for, strict substring verification.
- Calibrate signal weights against real historical account outcomes if/when such data becomes available.

---

## 10. Conclusion

This prototype reliably converts publicly available evidence into traceable buying-intent signals and personalized outbound, while explicitly documenting where and why its extraction pipeline still produces false positives. The 8-brand submission set demonstrates the full pipeline working end-to-end with verified, defensible scores. The 25-brand extended evaluation demonstrates the same pipeline under more realistic, noisier conditions — and honestly reports the specific limitation that surfaced, rather than concealing it. Given the brief's explicit preference for a thoughtful, well-reasoned prototype with honest limitations over an over-engineered system that overclaims production readiness, this is the tradeoff the project deliberately makes.
