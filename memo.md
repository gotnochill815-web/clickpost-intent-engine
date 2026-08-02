# ClickPost Intent Capture & Outbound Activation — Technical Memo

## 1. Signal Taxonomy & Why It's Structured This Way

Buying intent for ClickPost's ICP (CX/CS Heads, CTOs, Founders at $5–100M GMV D2C brands) isn't just "any public data point" — it's evidence that the brand is currently experiencing operational strain that logistics/returns software would address, or is actively re-evaluating its stack. I ranked signal categories by causal proximity to that decision, not by ease of collection:

1. **Tech-stack signals** (competitor detected/being replaced) — closest to an active buying decision.
2. **Complaint/friction signals** (stated shipping delays, return difficulty) — direct evidence of pain.
3. **Trigger events** (new CX/Ops leadership) — re-evaluation window.
4. **Hiring signals** (Returns Manager, Logistics Ops, 3PL Analyst) — operational strain evidence.
5. **Growth signals** (funding, expansion) — weakest, and explicitly *not* treated as a standalone signal, because funding alone doesn't imply logistics pain — it's a leading indicator at best, and the brief specifically warns against generic "company raised funding" reasoning.

A deliberate design rule, learned the hard way (see §4): **a neutral operational fact — a stated return fee, a standard 30-day window, a policy sentence — is not a signal.** Only text explicitly describing complaint, difficulty, inefficiency, or an unmet need counts. This distinction turned out to be the hardest part of the project to get right, and is discussed below.

## 2. Methodology

**Pipeline:** Fetch (curated URLs → BeautifulSoup, with automatic fallback to ATS platforms like Greenhouse/Lever/SmartRecruiters when a careers page is a marketing shell) → LLM Extraction (structured JSON, verbatim-quote-only) → Deterministic Rule Filter → Evidence Verification (substring match against raw source) → Rule-Based Scoring → ICP Eligibility Gate → Ranking → Outreach Generation.

**Sample:** 8 of the 25 provided brands (Brooklinen, Vuori, Rothy's, Solo Stove, Blueland, Caraway, Graza, Kosas), selected for reliable public-data availability, per the brief's stated preference for a well-reasoned smaller sample over forced full coverage. URLs for all 25 brands were researched and retained; the working set was chosen for depth, not breadth.

**Sources used:** returns/policy pages and careers pages (2 source types). Reddit was attempted via curated URLs but consistently returned HTTP 403 for anonymous requests; this source was dropped after one remediation attempt (User-Agent header) failed to resolve it, and is documented as a limitation rather than pursued further given the project's time box.

## 3. Scoring Logic

Signals are weighted by category (tech-stack/complaint signals highest, growth signals lowest, consistent with §1), verification status (verified = full weight, manual-review = half weight, rejected = zero), and each unique signal category is counted once per account rather than summed per mention — an early version double-counted repeated mentions of the same underlying issue, which we corrected after finding it inflated scores without adding real evidence (see §4).

This produces a score a sales leader can interrogate line by line: every point traces to a specific verbatim quote and its source page, not a black-box LLM judgment.

## 4. What We Got Wrong, and What It Taught Us

The single most important engineering finding in this project: **verification confirms a quote's provenance, not its correctness.** Our verifier checks that extracted evidence appears verbatim in the source document — but a real, verbatim quote can still be a misclassified signal.

We hit this twice. First, a stated $9.95 return fee at Brooklinen was initially flagged as `returns_issue` — a standard, non-complaint policy statement. We fixed this with explicit negative examples in the extraction prompt and a deterministic post-extraction filter that discards policy-language and vague-heading matches regardless of what the model labels them (this filter also caught a heading ("Open Roles") and a policy sentence ("international returns only") being misread as signals on other brands).

Second, and more significantly, an exploratory run across all 25 brands surfaced the same failure mode at scale on long FAQ-style pages: Momofuku Goods scored anomalously high almost entirely on repeated policy statements ("we do not accept returns on any of our products," restated three times in different sections) and reassurance language ("carriers often mark orders Delivered when still in transit") — text that resembles complaint language on the surface but is, on inspection, the brand proactively explaining normal policy, not describing an operational failure. Our deterministic filter, tuned against the 8-brand sample, did not generalize cleanly to longer, noisier FAQ documents. We do not include this 25-brand run's scores in our submitted results for this reason; we view it as a genuine finding about the limits of filter tuned on a small sample, worth flagging rather than hiding.

**Practical implication:** a "verified" signal is a necessary but not sufficient condition for trust. A production system would need either a second-pass classification check or a larger, more diverse tuning set for the deterministic filter before scoring at broader scale.

## 5. ICP Eligibility

Per the brief's instruction to assume ICP qualification unless research clearly shows otherwise, our gate defaults every account to eligible and only flags a deviation when there is specific, cited evidence. This is a curated/manual check (D2C, physical products, assumed mid-market), not an automated GMV lookup — building real automated scale detection would require funding/revenue-database integrations outside this project's scope and budget.

One account was flagged: **Rothy's**, based on publicly available evidence of unicorn-scale valuation (~$1B), an established multi-country retail footprint, and company maturity — details that suggest it may exceed the $5–100M GMV target band. Consistent with the brief's conservative instruction, we did not exclude Rothy's, but flagged it for manual review rather than silently including or excluding it.

## 6. Output

Of the 8 evaluated brands, 3 (Graza, Caraway, Blueland) produced verified, defensible buying-intent signals — specific job postings (3PL Analyst, Process Engineer) and specific operational statements (barcode-liability language, perishable-product return refusal). The remaining 5 either genuinely showed no qualifying signal under our taxonomy (Brooklinen, Vuori, Rothy's, Kosas) or could not be fully evaluated due to external access blocks (Solo Stove: HTTP 403 on returns, SSL certificate mismatch on careers).

**We generated outbound sequences for 3 accounts, not 5.** We chose not to manufacture outreach for zero-signal accounts to reach the requested count — doing so would have meant writing personalized-sounding copy with no real evidence behind it, the exact failure mode this project is designed to avoid. We view 3 grounded sequences as a stronger deliverable than 5 where 2 would be fabricated.

## 7. Limitations & Tradeoffs

- Only 2 source types (returns, careers) vs. the brief's suggested 2–3; Reddit was blocked and not substituted.
- No automated GMV/revenue check; ICP gate relies on curated assumptions.
- Deterministic filter is tuned to an 8-brand sample and known not to generalize to longer FAQ documents (§4).
- LLM extraction behavior was inconsistent across providers (Gemini, Groq, OpenAI) when switched mid-project due to rate limits; the same false-positive pattern reappeared each time a provider changed, requiring the negative-example prompt and code-level filter described above.

## 8. What We'd Build Next

- Second-pass classification check (not just verification) before scoring, to catch semantically-wrong-but-verbatim quotes.
- Automated GMV/scale estimation (e.g., via a paid enrichment API) to replace the curated ICP assumptions.
- Broaden the deterministic filter's training examples using the FAQ false-positive patterns discovered in the 25-brand exploratory run.
- Re-attempt Reddit via an authenticated API client rather than anonymous requests.
