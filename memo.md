

Memo · MD
# ClickPost Intent Capture & Outbound Activation — Technical Memo
 
**Prepared by:** Prakhya Khandelwal
 
## 1. What This Project Sets Out to Do
 
The idea behind this project is fairly simple to state, even if it isn't simple to do well: instead of an SDR guessing which D2C brands might be worth reaching out to, can we look at public information — a returns policy, a careers page — and figure out, with actual evidence, whether a brand is showing signs that they'd benefit from ClickPost. Not "this company exists and fits the ICP," but "this company has a specific, checkable reason to talk to us right now."
 
That distinction mattered a lot through this build. It's easy to build something that looks impressive and outputs a score for every brand. It's a lot harder to build something where you can point to the exact sentence on a company's website that justifies the score, and be confident that sentence actually means what you're claiming it means. Most of the real work in this project turned out to be in that second part.
 
## 2. How We Defined Buying Intent
 
Before writing any code, the first question was: what does "buying intent" even look like for a $5–100M GMV D2C brand whose CX Head or Founder might be evaluating ClickPost? We didn't want to fall into the trap of treating "company raised funding" as a proxy for buying intent — that's the exact generic signal the brief specifically calls out as unimpressive, and honestly, it's tempting to lean on because it's the easiest thing to find.
 
So the taxonomy was built around a simple test: does this evidence point to actual operational strain in shipping, returns, or post-purchase experience — not just general company health. Signals were ranked by how directly they connect to that:
 
- **Hiring for logistics roles** (3PL Analyst, Process Engineer, Warehouse roles) — a company doesn't create these roles unless there's real operational load to manage.
- **Hiring for customer support/CX roles** — a slightly weaker version of the same idea; a growing support team can mean growing post-purchase friction.
- **Returns-issue signals** — specific statements describing operational limitations in how returns are handled (not the return policy itself, but evidence of friction in it).
- **Reverse logistics signals** — structured evidence of how a company manages the return-processing workflow itself.
Things like funding announcements, retail expansion, and leadership hires outside CX/Ops were considered during development but deliberately left out of the final scoring. They're not irrelevant to a company's story, but they don't tell you anything specific about logistics pain, and including them would have meant scoring accounts on the exact kind of generic evidence this project was meant to move past.
 
## 3. How the Pipeline Actually Works
 
The final submitted pipeline pulls from two sources per brand — the returns/shipping policy page and the careers page — fetched directly via `requests` and `BeautifulSoup`, with an automatic fallback that follows careers pages through to their actual ATS platform (Greenhouse, Lever, SmartRecruiters) when the direct page is just a marketing landing shell with no real job listings.
 
During development we also experimented with pulling from About pages, Press pages, company blogs, and Reddit. Some of this turned up genuinely interesting content — a funding announcement here, a retail-expansion story there — but it also introduced a lot more noise, and more importantly, it introduced signal types (growth announcements, leadership hires unrelated to operations) that our own taxonomy had already decided not to weight highly. Rather than let that noise creep into the final scoring, the submitted prototype sticks to the two sources that consistently produced clean, verifiable evidence.
 
Once text is fetched, it goes through:
1. **LLM extraction** — pulling candidate signals as verbatim quotes, never paraphrased.
2. **A deterministic rule filter** — a plain Python layer that rejects known non-signal patterns (policy language, generic careers CTAs like "Apply Now," bare FAQ headings) regardless of what the model labeled them.
3. **Verification** — checking that each surviving signal's evidence is a real, exact substring of the source document, not something the model invented.
4. **Scoring** — a simple weighted sum, one weight per unique signal category actually present, no per-mention inflation.
5. **ICP eligibility gate** — every account defaults to eligible; flagged only when specific evidence suggests otherwise (see Section 5).
6. **Ranking and outreach generation** — for accounts that clear the bar, a LinkedIn message and a follow-up email are generated, constrained to reference only the verified evidence and nothing invented.
## 4. What Went Wrong Along the Way (And Why It Matters)
 
This is probably the most important section of the memo, because the mistakes taught us more about the actual reliability of this kind of system than the parts that worked cleanly on the first try.
 
**Verification checks that a quote is real — not that it's correctly understood.** Early on, a stated $9.95 return fee on Brooklinen's site got misclassified as a "returns issue," even though it's a perfectly normal, non-remarkable policy statement, not a complaint. It passed verification fine, because the sentence really was on the page — the problem was entirely in how the model interpreted it. We fixed this with explicit negative examples in the extraction prompt and a deterministic filter that catches this pattern regardless of the model's judgment. The same class of mistake showed up again later with "Apply Now" being read as a hiring signal, and with a "Director of Formulation" role being misclassified as an executive trigger event when we experimented with a broader taxonomy — a role in product formulation has nothing to do with logistics or CX, and it shouldn't have counted.
 
**Scoring stability turned out to be a real problem, not a hypothetical one.** During development, Graza consistently produced two clean, manually-verified signals — a 3PL Analyst hiring and a stated inability to accept returns on a perishable product. But across different automated runs, largely due to an evolving deduplication bug and shifting filter logic, its automated score bounced between 13, 21, and 29 for the same underlying evidence. We caught this by comparing automated runs against our own hand-verified numbers, and the discrepancy was serious enough that we made a deliberate call: **the final results submitted here were locked after manual verification, not taken from the last automated run.** A scoring system that gives different answers on different runs for the same evidence isn't something we'd want a sales leader relying on, and we'd rather say so plainly than quietly submit whichever run happened to look best.
 
**Filter improvements can just as easily break something that already worked.** At one point, tightening the filter to catch more false positives on longer FAQ-style pages also deleted Graza's genuine, previously-verified perishable-return signal — a real regression, not an improvement. That was the moment we decided to stop iterating on the extraction and filtering logic entirely and lock in the last state we'd actually checked by hand. The honest takeaway here is that without a proper regression-tested gold dataset, every change to a prompt or a filter is as likely to quietly break something correct as it is to fix something wrong — and we didn't have the runway in this project to build that kind of test harness properly.
 
To make this concrete rather than abstract, here is a side-by-side from one experimental run where we temporarily expanded the source set to include About, Press, and Blog pages and broadened the taxonomy to include `growth_signal` and `trigger_event` categories:
 
*Correctly retained (matches our locked, submitted results):*
```json
{"signal": "hiring_logistics", "evidence": "3PL Analyst", "brand": "Graza", "source": "careers", "verification": "verified"}
{"signal": "returns_issue", "evidence": "Unfortunately, we are not able to accept returns whereas Graza is a perishable food product.", "brand": "Graza", "source": "returns", "verification": "verified"}
```
 
*Incorrectly classified (excluded from our submitted results, kept here only as evidence of the failure mode):*
```json
{"signal": "trigger_event", "evidence": "Director of Formulation", "brand": "Blueland", "source": "careers", "verification": "verified"}
{"signal": "growth_signal", "evidence": "Blueland Announces Retail Expansion Into Whole Foods With Refillable Hand Soap", "brand": "Blueland", "source": "press", "verification": "verified"}
{"signal": "growth_signal", "evidence": "Blueland Raises $20 Million for New Category and Retail Expansion to Eliminate More Single-Use Plastic", "brand": "Blueland", "source": "press", "verification": "verified"}
{"signal": "hiring_customer_support", "evidence": "assist and educate customers while providing the highest level of customer experience.", "brand": "Jones Road Beauty", "source": "careers", "verification": "verified"}
```
 
Each of these passed our verification step cleanly — the evidence really was present, verbatim, on the source page — which is exactly the point made above: verification confirmed *provenance*, not *correctness*. "Director of Formulation" is a product/R&D role with no connection to logistics or CX and should never have been scored as an executive trigger event. The two Blueland press signals are real announcements, but they're exactly the kind of generic growth/funding evidence our own taxonomy (Section 2) explicitly ranks lowest and treats with suspicion — including them would have meant scoring Blueland higher on the same category of evidence the brief specifically warns against over-weighting. And "assist and educate customers... highest level of customer experience" is job *responsibility* language pulled from a paragraph, not an actual job title, despite passing our hiring-signal filter at the time.
 
We also saw a related, lower-severity version of the same issue on Rothy's: a "Get Started → returns portal" instruction and a Happy Returns privacy-policy disclaimer were extracted as `reverse_logistics` evidence. The first is a UI navigation step, not a stated fact about the brand's operations, and the second is boilerplate legal language, not evidence of anything. Our submitted result for Rothy's instead uses a different, more substantive piece of evidence from the same page — a note that certain items ineligible for return can instead be listed for resale on Poshmark — which is a genuine description of a return-limitation workaround rather than an instruction or a legal disclaimer.
 
None of the incorrect examples above appear in our submitted results. We include them here specifically because they're useful, concrete evidence of *why* we don't trust an automated pipeline's output without manual verification, and why our final numbers were locked by hand rather than taken from the last run of an evolving system.
 
## 5. ICP Eligibility
 
Per the brief's own guidance — assume ICP qualification unless research clearly shows otherwise — our eligibility check defaults every account to eligible, using curated checks (D2C, physical product, presumed mid-market) rather than an automated GMV lookup, which would need paid enrichment tools we didn't have access to.
 
One account was flagged rather than excluded: **Rothy's**, based on real, specific evidence — a roughly $1B valuation, a retail footprint spanning multiple countries, and general company maturity — that suggests it may sit above the $5–100M GMV band this ICP targets. We didn't exclude it, since the brief is explicit that ambiguous evidence should be flagged, not acted on unilaterally, but it's noted clearly in our results.
 
## 6. Results
 
We evaluated 8 of the 25 provided brands, chosen for reliable public-data availability — URLs for all 25 were researched during scoping, but depth on a smaller, carefully verified set was prioritized over shallow coverage of all 25, in line with the brief's own stated preference for a well-reasoned prototype over one that overclaims completeness.
 
| Rank | Brand | Intent Score | Verified Signal(s) |
|---|---|---|---|
| 1 | Graza | 13 | 3PL Analyst hiring; stated inability to accept returns (perishable product) |
| 2 | Caraway | 13 | Barcode-liability complaint (returns friction); Technical Project Leader hiring |
| 3 | Rothy's | 7 | Poshmark resale workaround for return-ineligible items — flagged for ICP review |
| 4 | Blueland | 6 | Process Engineer hiring |
| 5 | Brooklinen | 0 | No qualifying signal found |
| 6 | Vuori | 0 | No qualifying signal found |
| 7 | Kosas | 0 | No qualifying signal found |
| 8 | Solo Stove | 0 | Blocked — HTTP 403 on returns page, SSL certificate mismatch on careers subdomain |
 
Outreach (one LinkedIn message and one follow-up email, each referencing the specific verified evidence) was generated for the top 4 accounts. **We generated 4 sequences rather than 5**, because only 4 of the 8 evaluated accounts produced genuinely verified evidence. We considered padding the list to 5 using weaker or unverified signals from a broader exploratory run, but decided against it — doing so would mean writing personalized-sounding outreach with no real evidence behind it, which is precisely the failure mode this project exists to prevent. We think 4 grounded, defensible sequences serve the actual goal better than 5 where one would be fabricated.
 
## 7. Limitations & Tradeoffs
 
- **Two source types, not the suggested 2–3.** Reddit was attempted through manually curated URLs, but consistently returned HTTP 403 for anonymous requests. One fix attempt (adding a real browser User-Agent header) didn't resolve it, and we didn't pursue it further given the project's time box.
- **No automated GMV verification** — the ICP gate relies on curated assumptions rather than a live revenue lookup (see Section 5).
- **Extraction and filtering are not perfectly reliable**, and we found this out the hard way (see Section 4). We'd rather report this honestly than paper over it with a filter we didn't have time to properly validate.
- **Scoring reproducibility is a known open issue.** Repeated automated runs did not always reproduce our hand-verified numbers for the same evidence — this is documented in Section 4, and it's the reason our submitted results were manually locked rather than taken from an automated batch run.
- **Weights are hand-assigned**, reflecting a defensible business judgment about which signals matter most, not coefficients learned from real conversion data, which we didn't have access to.
## 8. Compliance Note
 
Everything collected here is publicly available — company returns pages, careers pages. No login-gated content, no private data, no personal information beyond what a brand itself has published. Reddit access was attempted only through standard, unauthenticated requests, and dropped once it became clear that wasn't working reliably rather than pursuing a workaround.
 
## 9. What We'd Build Next
 
Given more time, the next steps would be: a small hand-labeled gold dataset with automated regression tests, so future prompt or filter changes can be checked against known-correct answers instead of judged by eye each time; a real GMV/scale-estimation step to replace the curated ICP assumptions; broader, more reliable source coverage (particularly an authenticated path to Reddit); and continuous monitoring of accounts over time rather than a one-time snapshot, so new intent signals can be surfaced as they appear rather than requiring a fresh full run.
 
## 11. Appendix: Extended Exploratory Run (Not Part of Submitted Results)
 
For transparency, this appendix shows the output of one exploratory run that expanded source coverage to About, Press, and Blog pages and broadened the taxonomy to include `growth_signal` and `trigger_event` categories. **None of this data is part of our submitted results in Section 6** — it's included here only so the reasoning behind our decision to lock the smaller, hand-verified set is fully visible, not just asserted.
 
| Brand | Score | Status | Note |
|---|---|---|---|
| Graza | 13 | ✅ Reliable | Matches our locked, submitted result exactly (3PL Analyst + perishable-return refusal). |
| Blueland | 11 | ❌ Not reliable | Includes "Director of Formulation" misclassified as a trigger event, and two funding/retail-expansion signals that our own taxonomy explicitly treats as weak, generic evidence (see Section 4). Submitted result uses only the verified Process Engineer hiring signal, score 6. |
| Rothy's | 7 | ⚠️ Partially reliable | Score matches our submitted result, but the underlying evidence differs: this run cites a UI navigation instruction and a legal privacy-policy disclaimer, neither of which is a genuine signal. Our submitted result instead uses a different, more substantive piece of evidence from the same page (a Poshmark resale workaround for return-ineligible items). |
| Caraway | 5 | ❌ Not reliable | Cites only "QA Manager, Customer Experience," a single unverified title. Our submitted result (score 13) is built on two signals we manually verified directly against source text: a barcode-liability complaint and a Technical Project Leader hiring. |
| Vuori | 5 | ⚠️ Plausible but unverified | "Customer Service Agent" is a real, generic hiring signal consistent with earlier findings in this project, but it was not re-verified in this specific run. Not included in submitted results because our locked evaluation found no qualifying signal for Vuori. |
| Jones Road Beauty | 5 | ❌ Not reliable | Cites "assist and educate customers... highest level of customer experience" as a hiring signal — this is job-responsibility marketing language, not an actual job title, and should not have passed our filter. Not part of our evaluated brand set. |
| Brooklinen, Solo Stove, Kosas, Liquid Death, Our Place, Magic Spoon | 0 | ✅ Consistent | All scored 0 in this run, consistent with our submitted results for Brooklinen, Solo Stove, and Kosas (the other three are outside our primary 8-brand set). |
 
The pattern here is consistent with the rest of Section 4: broadening sources and taxonomy categories introduced new, plausible-looking signals that did not hold up under manual scrutiny, while our original, narrower, hand-verified set remained stable throughout. This is why the results in Section 6 — not this appendix — represent what we are actually standing behind in this submission.
 
## 12. Closing
 
This project is, honestly, as much a story about what didn't work cleanly the first time as it is about what did. We hit real bugs — a scoring regression, a filter that deleted a signal we'd already verified, a model that misread a routine return-fee policy as a complaint — and each one taught us something concrete about where an LLM-based pipeline like this needs guardrails before it can be trusted. We'd rather hand over a smaller, honestly-verified set of results with those lessons written down clearly than a bigger, shinier-looking table we hadn't actually checked.
 
