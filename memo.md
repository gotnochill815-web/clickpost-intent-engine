# ClickPost Intent Capture & Outbound Activation
## Technical Memo

**Prepared by:** Prakhya Khandelwal

---

## 1. Executive Summary

Modern Sales Development Representatives (SDRs) often face thousands of potential accounts that technically fit an Ideal Customer Profile (ICP), yet only a small fraction are actively exhibiting signs of buying intent. Traditional prospecting methods primarily rely on firmographic attributes such as company size, industry, revenue, or employee count. While these characteristics identify companies that could become customers, they provide little evidence that those companies currently have an operational need for a post-purchase platform like ClickPost.

The objective of this project was to design and implement an end-to-end AI-powered pipeline capable of automatically identifying operational buying-intent signals from publicly available information. Instead of simply ranking companies based on static business characteristics, the system searches for observable evidence that may indicate logistics or post-purchase challenges. Examples include hiring for logistics-related roles, hiring customer support personnel, operational statements within returns policies, and evidence of structured reverse logistics processes.

The pipeline combines Large Language Models (LLMs) with deterministic software engineering techniques. GPT is used to extract candidate buying-intent signals from company webpages, while rule-based filters and exact evidence verification reduce hallucinations and false positives. Verified signals are then scored using an explainable rule-based taxonomy, evaluated against ClickPost's Ideal Customer Profile (ICP), ranked, and finally used to generate personalized outbound sequences consisting of a cold email and LinkedIn connection request.

A key design goal throughout the project was explainability. Every score assigned to a company can be traced back to specific publicly available evidence rather than opaque model predictions. Likewise, every generated outreach message is explicitly grounded in verified evidence extracted from company webpages, preventing unsupported business assumptions.

---

## 2. Defining Buying Intent

The first design decision was determining what should actually count as buying intent for ClickPost's target customers.

ClickPost operates in the post-purchase logistics space, helping Direct-to-Consumer (D2C) brands improve shipment visibility, carrier integrations, returns management, and customer communication. Consequently, not every company announcement should increase buying intent. The objective was to identify operational signals that could reasonably indicate logistics challenges or investment in post-purchase operations.

Several categories of potential signals were explored during development. Rather than treating all signals equally, they were evaluated according to their direct relationship with ClickPost's value proposition.

**Hiring Logistics**

Hiring for logistics-related positions such as Supply Chain Analyst, Warehouse Operations, Fulfillment, or 3PL roles often reflects growing operational complexity. These roles frequently appear when companies begin scaling their logistics infrastructure or optimizing fulfillment operations.

This category was considered one of the strongest indicators because logistics hiring directly aligns with ClickPost's platform capabilities.

**Hiring Customer Support**

Customer support hiring represents another operational signal, although slightly weaker than logistics hiring.

Growing customer support teams may indicate increasing customer interactions regarding shipping, delivery, or returns. While customer support expansion alone does not necessarily imply logistics pain, it frequently accompanies increased post-purchase activity.

**Returns Issues**

Returns policies occasionally contain operational statements rather than standard legal language.

Examples include:

- inability to accept certain returns
- customer restrictions
- operational return limitations

Such evidence may indicate friction in existing return workflows and therefore represents a stronger buying-intent signal than generic policy text.

Routine policy language, however, was deliberately excluded through deterministic filtering.

**Reverse Logistics**

Evidence describing structured return workflows, return portals, carrier integrations, or dedicated reverse logistics processes can also indicate investment in post-purchase operations.

These signals were included because they directly relate to ClickPost's returns automation capabilities.

**Signals Considered but Excluded**

During development, additional signal categories were explored, including:

- funding announcements
- retail expansion
- executive hires
- company blog posts
- press releases
- Reddit discussions

Although these sources occasionally surfaced interesting business information, they also introduced significantly more noise and weaker evidence of actual operational buying intent.

For example, a company announcing retail expansion or raising funding does not necessarily indicate logistics pain or an active evaluation of post-purchase software.

To remain aligned with ClickPost's business objectives and the evaluation rubric, the final scoring pipeline focuses on operational evidence extracted primarily from Returns and Careers pages.

---

## 3. Methodology

The pipeline follows a modular architecture consisting of seven stages:

```text
                 Brand URLs
                      │
                      ▼
               Page Fetching
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
               ICP Gate
                      │
                      ▼
                 Ranking
                      │
                      ▼
      Grounded Outreach Generation
```

Each stage performs a single responsibility:

- **Page Fetching:** Retrieves Returns and Careers pages from publicly available websites.
- **GPT Signal Extraction:** Extracts candidate buying-intent signals while preserving verbatim evidence.
- **Deterministic Rule Filtering:** Removes common false positives such as generic policy text, legal boilerplate, FAQ headings, and career-page boilerplate.
- **Evidence Verification:** Confirms every extracted quote exists exactly within the original webpage using substring matching.
- **Intent Scoring:** Assigns explainable weights to verified signal categories.
- **ICP Gate:** Evaluates whether the company matches ClickPost's Ideal Customer Profile.
- **Ranking:** Orders accounts based on verified intent scores.
- **Grounded Outreach Generation:** Produces personalized cold emails and LinkedIn messages using only verified evidence.

## 4. Data Collection

For each company, the pipeline attempts to retrieve publicly available webpages containing operational information.

The primary sources used in the final prototype are:

- Returns / Shipping Policy
- Careers Page

Many organizations host careers on external Applicant Tracking Systems (ATS) such as Lever, Greenhouse, SmartRecruiters, or BuiltIn.

The crawler automatically detects these redirects and follows them to retrieve actual job listings instead of generic landing pages.

During development, additional sources including Press, About, Blog, and Reddit were explored. While these occasionally produced relevant observations, they also generated substantially more false positives. As a result, the production scoring pipeline prioritizes the two sources that consistently yielded the highest-quality operational evidence.

---

## 5. Signal Extraction

Signal extraction is performed using GPT.

Rather than summarizing webpages, the model is instructed to identify candidate buying-intent signals while preserving the original wording from the source webpage.

Each extracted signal contains:

- Brand
- Signal category
- Evidence
- Source webpage

Using verbatim evidence allows every extracted observation to be independently verified before it influences downstream scoring.

---

## 6. Rule-Based Filtering

Raw LLM extraction is intentionally permissive, allowing GPT to identify any text that appears relevant. While this improves recall, it also introduces false positives arising from webpage boilerplate, navigation text, and legal content. To improve precision, a deterministic rule-based filtering layer was implemented.

The filtering module removes evidence that matches known non-operational patterns before verification and scoring.

Examples include:

- Generic career page headings such as Apply Now or Open Roles
- FAQ section titles
- Standard return-policy language
- Customer support instructions
- Legal and privacy statements
- Generic refund information
- Duplicate evidence

Unlike prompt engineering alone, deterministic filters ensure that common false positives are rejected consistently regardless of LLM behavior.

This hybrid architecture combines the flexibility of LLM extraction with the reliability of rule-based software, significantly improving overall signal quality.

---

## 7. Evidence Verification

A key engineering objective was ensuring that every signal contributing to an intent score could be traced directly back to publicly available evidence.

After filtering, every extracted evidence string undergoes exact substring verification against the original webpage.

Each signal is labeled as either:

- **Verified** – the extracted evidence exists exactly within the retrieved webpage.
- **Manual Review** – the evidence could not be confidently matched and therefore should be inspected manually.

Only verified evidence contributes to the final intent score.

This verification layer serves two important purposes:

- It reduces hallucinated evidence generated by the LLM.
- It enables complete auditability, allowing every ranked account to be traced back to its original source.

Although verification confirms that the extracted text exists, it does not guarantee that the text has been interpreted correctly. Consequently, verification is complemented by deterministic filtering and explainable scoring rather than being treated as a complete solution.

---

## 8. Explainable Intent Scoring

After verification, accounts are assigned intent scores using a deterministic weighted taxonomy.

The final scoring scheme is intentionally simple and transparent.

| Signal Category | Weight |
|-----------------|--------|
| Returns Issue | 7 |
| Reverse Logistics | 7 |
| Hiring Logistics | 6 |
| Hiring Customer Support | 5 |

Each signal category contributes only once per company, regardless of how many matching statements are extracted.

For example, if multiple sections of a returns policy describe the same operational limitation, the category contributes a single score rather than inflating the company's ranking.

This prevents long FAQ pages from unfairly dominating shorter webpages while preserving all supporting evidence for reviewer inspection.

The scoring system is fully explainable. Every point assigned to an account can be traced directly to verified evidence, making the rankings interpretable by both engineering and sales teams.

---

## 9. ICP Eligibility Gate

Not every company exhibiting operational signals is necessarily an ideal customer for ClickPost.

An ICP evaluation layer therefore assesses companies against three manually curated criteria:

- Direct-to-Consumer (D2C)
- Mid-market business
- Physical products

Companies remain in the final ranked output even when additional review may be required.

This design prioritizes transparency over automatic exclusion, ensuring potentially valuable accounts are not discarded solely because publicly available information is incomplete.

---

## 10. Final Results

The prototype successfully processed twelve representative D2C brands selected from the ClickPost assessment.

The final ranked output is shown below.

| Rank | Brand | Score |
|------|-------|-------|
| 1 | Graza | 13 |
| 2 | Blueland | 11 |
| 3 | Rothy's | 7 |
| 4 | Vuori | 5 |
| 5 | Caraway | 5 |
| 6 | Jones Road Beauty | 5 |
| 7 | Brooklinen | 0 |
| 8 | Solo Stove | 0 |
| 9 | Kosas | 0 |
| 10 | Liquid Death | 0 |
| 11 | Our Place | 0 |
| 12 | Magic Spoon | 0 |

The highest-ranked accounts exhibited verified operational buying-intent signals extracted from publicly available webpages.

Lower-ranked companies either lacked verified operational evidence or contained only information that was filtered as non-actionable.

---

## 11. Grounded Outbound Generation

For every account containing verified buying-intent signals, the pipeline automatically generates:

- A personalized cold email
- A LinkedIn connection request

Unlike generic sales outreach, each message is explicitly grounded in the evidence captured during extraction.

For example, if a company is hiring for a logistics role, the outreach references that hiring signal directly rather than making unsupported assumptions about company growth or operational challenges.

The prompting strategy explicitly prohibits:

- unsupported business conclusions
- speculative operational pain
- inferred company priorities
- invented logistics problems

Instead, the outreach introduces ClickPost's capabilities in a neutral manner and invites further discussion only if the company is actively evaluating solutions in that area.

This grounding strategy improves factual correctness while producing outreach that remains relevant to the observed operational signal.

---

## 12. Engineering Tradeoffs and Key Learnings

Building a reliable buying-intent detection system proved to be less about extracting information and more about ensuring that extracted information was meaningful, trustworthy, and explainable.

One of the earliest observations was that **LLM extraction alone is insufficient**. While the model successfully identified relevant text from webpages, it occasionally assigned incorrect semantic meaning to otherwise valid evidence.

For example, routine statements such as return fees or generic hiring page content were initially classified as buying-intent signals despite having little relevance to ClickPost's value proposition.

This led to the introduction of a deterministic filtering layer positioned between extraction and verification.

The combination of:

- GPT extraction
- rule-based filtering
- exact evidence verification

proved significantly more reliable than relying on prompt engineering alone.

Another important engineering decision involved scoring.

Instead of allowing every extracted sentence to contribute independently, the scoring system awards points **once per signal category**. This prevents lengthy FAQ pages from producing artificially inflated intent scores while preserving every verified evidence snippet for inspection.

Throughout development, explainability consistently took priority over complexity. Although more sophisticated approaches such as embedding similarity, semantic ranking, or LLM-as-a-judge were considered, a deterministic weighted scoring system was selected because every decision can be traced directly back to publicly verifiable evidence.

This makes the rankings easier to understand, debug, and defend during sales discussions.

---

## 13. Challenges Encountered

Several practical challenges emerged during implementation.

### Public Website Accessibility

Not every company website could be fetched successfully.

Some brands returned:

- HTTP 403 errors
- SSL certificate errors
- anti-bot protection pages

Instead of silently failing, the pipeline records incomplete fetches so reviewers can distinguish unavailable data from companies with genuinely missing signals.

### Applicant Tracking Systems

Many companies host their careers pages on external Applicant Tracking Systems such as:

- Lever
- Greenhouse
- SmartRecruiters
- BuiltIn

The crawler therefore includes automatic redirect handling to retrieve actual job postings instead of generic careers landing pages.

### False Positive Extraction

False positives represented the largest technical challenge.

Examples encountered during development included:

- "Apply Now" interpreted as a hiring signal.
- Generic FAQ headings extracted as reverse logistics.
- Routine return policy language classified as operational returns issues.
- Product-related leadership positions being interpreted as logistics trigger events.

Rather than attempting to eliminate these purely through prompt engineering, deterministic filtering rules were introduced to remove known patterns before scoring.

### Balancing Precision and Recall

Improving precision sometimes reduced recall.

More aggressive filters successfully removed additional false positives but occasionally removed legitimate operational evidence as well.

This highlighted an important lesson:

A filtering strategy should always be evaluated using regression tests rather than relying solely on qualitative inspection of a single pipeline run.

---

## 14. Limitations

Although the prototype successfully demonstrates end-to-end buying-intent detection, several limitations remain before production deployment.

### Public Data Coverage

The pipeline relies entirely on publicly available webpages.

Some companies restrict automated access through HTTP 403 responses, SSL issues, or anti-bot protection, resulting in incomplete coverage for certain accounts.

### Limited Source Diversity

During development, additional sources including Press pages, Blog pages, About pages, and Reddit discussions were explored.

While these occasionally surfaced interesting business updates, they also introduced substantially more false positives and weaker operational evidence.

The final scoring pipeline therefore prioritizes Returns and Careers pages, which consistently produced the highest-quality logistics signals.

### LLM Extraction Still Requires Verification

Verification confirms that extracted text exists on a webpage.

However, it does **not** guarantee that the extracted evidence has been interpreted correctly.

During development, examples such as:

- "$9.95 return fee"
- "Apply Now"
- "Director of Formulation"

were initially classified as buying-intent signals despite being unrelated to ClickPost's target use case.

This limitation motivated the addition of deterministic filtering and exact evidence verification.

### Rule-Based Filters Require Maintenance

Rule-based filtering significantly reduced false positives but also introduced the possibility of over-filtering.

An overly aggressive filtering iteration removed previously verified operational evidence while attempting to eliminate policy-related text.

This demonstrates the need for automated regression testing whenever extraction prompts or filtering rules are modified.

### Heuristic Scoring

Intent scores are assigned using manually defined weights rather than historical CRM outcomes.

Although these weights are transparent and explainable, future versions should learn optimal signal importance directly from sales pipeline and conversion data.

### Manual ICP Evaluation

ICP eligibility currently relies on manually curated rules.

A production system would automatically infer company characteristics using external business intelligence platforms or CRM enrichment services.

### Snapshot Rather Than Continuous Monitoring

The prototype evaluates each company at a single point in time.

Buying-intent signals evolve continuously as companies publish new job openings, modify return policies, or announce operational initiatives.

A production deployment would monitor these changes automatically and update rankings accordingly.

### Limited Quantitative Evaluation

The project focuses on building a working engineering prototype rather than optimizing predictive performance.

Because no labeled benchmark dataset exists for buying-intent signals, evaluation relied on repeated pipeline execution, manual verification against source webpages, and inspection of intermediate artifacts rather than traditional metrics such as Precision, Recall, or F1-score.

---

## 15. Future Work

Several extensions would further improve the system.

- Retrieval-Augmented Generation (RAG) over company documentation.
- Automated regression testing using a gold-standard evaluation dataset.
- CRM feedback loops for learning signal weights from historical conversions.
- Automatic ICP inference using external enrichment providers.
- Continuous monitoring of company webpages for newly emerging signals.
- Confidence calibration for each extracted signal.
- Interactive dashboard for Sales Development Representatives to inspect evidence, rankings, and generated outreach.

---

## 16. Conclusion

This project demonstrates that publicly available operational information can be transformed into explainable buying-intent signals for Direct-to-Consumer brands.

Rather than relying solely on company size or firmographic attributes, the pipeline identifies operational evidence from Returns and Careers pages, verifies extracted observations against their original sources, applies deterministic filtering, ranks companies using an explainable scoring framework, and generates grounded outbound outreach based exclusively on verified evidence.

Perhaps the most important engineering lesson from this project is that **verification alone does not guarantee correctness**.

A sentence may exist on a webpage while still being incorrectly interpreted by an LLM. Reliable intent detection therefore requires multiple complementary safeguards, including deterministic filtering, evidence verification, explainable scoring, and transparent audit trails.

Although the prototype remains a research-oriented system rather than a production-ready platform, it establishes a modular foundation that can be extended with richer data sources, automated monitoring, CRM feedback, and continuous learning.

Overall, the project demonstrates how LLMs and traditional software engineering techniques can be combined to build an interpretable and practically useful sales intelligence pipeline aligned with ClickPost's business objectives.
