# Hiver SDE Intern Take-Home — Full Implementation Checklist

Use this as your working checklist. Check items off as you go (`[x]`). Nothing here is optional filler — every item exists because it's a common way this assignment loses points.

---

## PHASE 0 — Environment & Project Setup (Day 1, ~1-2 hrs)

- [ ] Create a public (or shareable private) GitHub repo, initialize with `.gitignore` (Python template) and MIT/Apache license
- [ ] Set up Python virtual environment (`venv` or `conda`)
- [ ] Create folder structure upfront:
  ```
  /data          (raw + processed, gitignored if large)
  /notebooks     (exploration only, not final logic)
  /src           (pipeline code: classify, retrieve, draft, escalate)
  /eval          (golden set, harness, judge)
  /report        (report.md, decision_log.md, figures)
  /outputs       (run logs, predictions, metrics)
  README.md
  requirements.txt
  ```
- [ ] Decide LLM provider (Claude API / OpenAI / open model via Ollama) and get API key working with a "hello world" call
- [ ] Set up `.env` + `python-dotenv` (or equivalent) — **never commit API keys**
- [ ] Set a global random seed (`random.seed`, `np.random.seed`) for reproducibility of sampling
- [ ] Write a `requirements.txt` / `pyproject.toml` as you go, not at the end
- [ ] Make your first commit ("project scaffold")

---

## PHASE 1 — Data Acquisition & Exploration (Day 1-2, ~2-4 hrs)

- [ ] Download the Kaggle "Customer Support on Twitter" dataset (`thoughtvector/customer-support-on-twitter`)
- [ ] Check dataset size/format (CSV, columns: `tweet_id`, `author_id`, `text`, `created_at`, `response_tweet_id`, `in_response_to_tweet_id`)
- [ ] Load into pandas, check row count, nulls, duplicates
- [ ] Understand thread structure: each conversation is a chain via `response_tweet_id` / `in_response_to_tweet_id` — write a small function to reconstruct threads from these pointers
- [ ] Get a list of unique brand handles (`author_id` for company accounts, e.g. `SpotifyCares`) and their message volumes
- [ ] Note: company replies come FROM the brand account; customer messages come from numeric anonymized IDs — confirm you understand which is which
- [ ] Check timestamp range / recency of data (matters for "is this still relevant" discussion in report)
- [ ] Decide and document your **subsample size** (e.g., 5,000-15,000 tweets for the chosen brand) — full dataset is not required and not expected
- [ ] Save the raw brand-specific subsample to `/data/raw/`

---

## PHASE 2 — Brand Selection & Validation (Day 2, ~2 hrs)

- [ ] Shortlist 2-3 candidate brands (e.g., SpotifyCares, AppleSupport, AmazonHelp)
- [ ] For each candidate, sample 30-50 threads and manually skim them
- [ ] Check: does the brand's resolution style repeat in recognizable patterns (needed for "grounding")? Or is every issue account-specific/unique (bad for grounding)?
- [ ] Check: is there enough volume per likely-intent to support 150-250 golden examples with reasonable per-class counts?
- [ ] Check: are replies mostly generic "please DM us" (bad — low signal) or do they contain real resolution content in-thread?
- [ ] **Make final brand decision and write down why** (this becomes a decision log entry)
- [ ] Filter your subsample down to only this brand's conversations
- [ ] Reconstruct full customer→brand→customer threads (not just single tweets) — you need multi-turn context for realistic classification/escalation later

---

## PHASE 3 — Intent Taxonomy Design & Validation (Day 2-3, ~3-4 hrs)

- [ ] Draft an initial taxonomy from your knowledge of the brand (start with 6-8 categories max, one being a catch-all "Other")
- [ ] Randomly sample 50-100 real customer messages from your filtered data
- [ ] Manually tag each with your draft taxonomy — **do this yourself, don't let an LLM do the first pass**
- [ ] Track: how many fall into "Other"? If >15-20%, your taxonomy is missing a real category — revise
- [ ] Check for overlapping/ambiguous categories (if you keep hesitating between two labels, merge them or add a clearer rule)
- [ ] Finalize taxonomy with **explicit written definitions + 2-3 example messages per intent** (this doubles as your labeling guide)
- [ ] Write down the taxonomy rationale — what you included, what you deliberately excluded, and why (decision log entry)
- [ ] Define your **escalation categories/rules** at this stage too (draft version — you'll calibrate thresholds later with real data)

---

## PHASE 4 — Data Preparation Pipeline (Day 3, ~3 hrs)

- [ ] Write a cleaning function: strip @mentions/URLs where appropriate (but keep for context if needed), handle emojis, handle non-English tweets (decide: filter out or keep? document decision)
- [ ] Deduplicate identical/near-identical tweets
- [ ] Reconstruct (customer_message, brand_reply, thread_context) triples — this is your core unit of analysis
- [ ] Filter out threads with no brand reply (can't learn resolution pattern from these) — but keep a note of how many you dropped and why (relevant to bias discussion later)
- [ ] Build a lightweight **"historical resolution" knowledge base**: group past (customer_message, brand_reply) pairs, e.g., embed customer messages and store with their resolutions for retrieval later (this is what "grounding" will pull from)
- [ ] Decide retrieval method: simple keyword/TF-IDF similarity vs. embedding-based similarity (embeddings likely better, but justify cost/complexity tradeoff in decision log)
- [ ] Save processed data to `/data/processed/`

---

## PHASE 5 — Golden Evaluation Set Creation (Day 3-4, ~4-5 hrs — do NOT rush this)

- [ ] Decide sampling strategy: stratified by intent (to guarantee coverage) vs. pure random (more realistic distribution) — recommend stratified with a documented minimum per class (e.g., ≥15 per intent)
- [ ] Sample 150-250 messages using that strategy, **excluding any messages you already saw while designing the taxonomy** (avoid contamination)
- [ ] For each example, hand-label:
  - [ ] Ground-truth intent
  - [ ] A reference/acceptable reply (or key facts a good reply must contain)
  - [ ] Ground-truth escalate/auto-handle decision + reason
- [ ] Write your labeling guide/rubric down as a separate doc (so it's reproducible, not "vibes")
- [ ] If possible, get a second person (friend, or do a second pass yourself a day later) to label a 20-30 example subset independently — compute agreement (Cohen's kappa or simple % agreement) — this proves your golden set isn't noisy
- [ ] Store the golden set as a clean CSV/JSON: `id, text, thread_context, gold_intent, gold_reply_reference, gold_escalate, gold_escalate_reason`
- [ ] Write the "how sampled and labeled" note required by the deliverables — do this now while it's fresh, not at report time

---

## PHASE 6 — Baseline Systems (Day 4, ~2-3 hrs)

- [ ] **Trivial baseline**: e.g., always predict the most frequent intent; always reply with a fixed generic template ("Thanks for reaching out, please DM us"); never escalate (or always escalate)
- [ ] **Simple baseline**: e.g., keyword/regex-based intent classifier (word lists per intent); reply = nearest-neighbor historical reply via TF-IDF; escalate = simple rule (contains "refund" or "$")
- [ ] Run both baselines on the golden set and record metrics (you'll need these numbers for the report comparison — do this before building the full system so you're not tempted to reverse-engineer favorable baselines later)
- [ ] Save baseline predictions to `/outputs/baselines/`

---

## PHASE 7 — Core Agent Pipeline (Day 4-6, the main build)

### 7a. Intent Classifier
- [ ] Decide approach: LLM zero/few-shot classification vs. fine-tuned small model — justify choice (cost, latency, data availability) in decision log
- [ ] Write the classification prompt with your taxonomy definitions + examples embedded (few-shot)
- [ ] Run on golden set, get predictions
- [ ] Handle edge case: what happens on API failure/timeout — retry logic, fallback to "Other" + escalate

### 7b. Grounded Reply Drafting
- [ ] Given a customer message, retrieve top-k similar historical (message, reply) pairs from your knowledge base (Phase 4)
- [ ] Construct a prompt that conditions the LLM on: customer message + thread context + retrieved historical resolutions + brand tone guidance
- [ ] Generate draft reply
- [ ] Add a guardrail: reply should not invent specific facts (order numbers, refund amounts, dates) not present in the input — decide how you'll check/enforce this
- [ ] Log which historical examples were retrieved for each reply (needed for failure analysis and explainability)

### 7c. Escalation Decision
- [ ] Implement your escalation rules (from Phase 3, refined with real data) — combine: intent-based rules, confidence-based rules, sentiment/keyword-based rules, multi-turn/repeat-contact rules
- [ ] Output a **structured decision**: `{escalate: true/false, reason: "..."}` — reason must be human-readable, not just a label
- [ ] Decide and document your confidence threshold calibration approach (e.g., plot classifier confidence vs. correctness on golden set to pick a cutoff)

### 7d. Pipeline Wiring
- [ ] Wire classify → retrieve → draft → escalate into a single callable pipeline function/script
- [ ] Add logging (input, intent, retrieved examples, draft reply, escalation decision, latency, token cost) to `/outputs/runs/`
- [ ] Add basic error handling everywhere an API call happens
- [ ] Run the full pipeline end-to-end on a small test batch (5-10 examples) and sanity-check outputs manually before running on the full golden set

---

## PHASE 8 — Evaluation Harness (Day 6-7, critical section — don't skimp)

- [ ] **Intent classification metrics**: accuracy, per-class precision/recall/F1, confusion matrix (plot it)
- [ ] **Escalation decision metrics**: precision/recall/F1 treating "should escalate" as positive class — false negatives (missed escalations) are worse than false positives, note this asymmetry explicitly
- [ ] **Reply quality — automated/cheap checks**: length sanity, does it avoid inventing specific facts not in input (simple fact-presence check), does it match brand tone (basic heuristics)
- [ ] **LLM-as-judge for reply quality**:
  - [ ] Design a rubric with explicit criteria (e.g., relevance, groundedness/factual consistency with retrieved history, tone match, helpfulness, conciseness) each scored 1-5
  - [ ] Write the judge prompt with the rubric embedded, feed it (customer message, thread context, generated reply, retrieved ground-truth reply) and get scores + justification
  - [ ] Run judge on all golden set replies (your system + both baselines) for fair comparison
- [ ] **Judge-human agreement check (mandatory, don't skip)**:
  - [ ] Hand-score 20-30 replies yourself on the same rubric, blind to the judge's scores
  - [ ] Compute correlation (Spearman/Pearson) or agreement rate between your scores and the judge's
  - [ ] Report this number honestly — if agreement is mediocre, say so and discuss why (this is a strength, not a weakness, if handled honestly)
- [ ] Aggregate everything into a single results table: baseline-trivial vs. baseline-simple vs. your-system, across all metrics
- [ ] Save all raw scores (not just aggregates) to `/eval/results/` for reproducibility

---

## PHASE 9 — Failure Analysis (Day 7-8, ~3 hrs)

- [ ] Sort golden set results by lowest reply-quality score and by misclassified intents
- [ ] Manually read through 30-50 worst cases
- [ ] Cluster failures into recurring patterns (aim for exactly 5 distinct failure modes, not a laundry list)
- [ ] For each of the 5, pull a **real example** (input, gold answer, your system's output) and write a **hypothesis** for why it happens (e.g., "retrieval pulled an irrelevant historical example because TF-IDF matched surface words not intent")
- [ ] Check for systematic bias: does the system perform worse on any particular intent, message length, or presence of certain keywords/emojis?
- [ ] Note any language/dialect/sarcasm handling failures explicitly — common in Twitter data

---

## PHASE 10 — Report Writing (Day 8-9, ~4-5 hrs)

Write as README section or separate `/report/report.md`, max 6 pages equivalent:

- [ ] **Problem framing**: what "good" means for this brand specifically (e.g., "good" = doesn't promise things Spotify can't deliver, resolves technical issues without human involvement, correctly escalates anything touching money); explicitly list what you chose NOT to build (e.g., no real account lookup, no multi-language support, no live API integration) and why
- [ ] **Results vs. baselines**: the comparison table from Phase 8, with 2-3 sentences of interpretation, not just numbers
- [ ] **Failure analysis section**: the 5 failure modes from Phase 9 with examples and hypotheses
- [ ] **"What is misleading about my headline number?" section (mandatory)** — be genuinely critical: e.g., golden set may be biased toward well-formed tweets, LLM judge may share the same blind spots as the model it's judging, escalation precision looks high because most golden examples don't need escalation (class imbalance), historical data may reflect stale/outdated Spotify policies, etc.
- [ ] **What you'd do next with one more week**: concrete, prioritized (not vague "more data" — be specific: e.g., "add a hallucination-detection step comparing draft reply against retrieved facts via NLI model")
- [ ] Proofread for length — trim to fit 6 pages if using a doc format

---

## PHASE 11 — Decision Log (Day 9, ~1-2 hrs)

- [x] Compile 10-15 non-obvious decisions from all the notes you took along the way (brand choice, taxonomy design, retrieval method, threshold calibration, subsample size, what counts as "escalate", how ties/ambiguous labels were handled, why LLM-as-judge over pure automated metrics, etc.)
- [x] Keep it to bullet points — decision + one-line reason each, no essay
- [x] Cross-check: does every "why did you..." question you can imagine being asked in the interview have an answer here?

---

## PHASE 12 — Repo Polish & Reproducibility (Day 9-10, ~2-3 hrs)

- [x] Write the README from scratch assuming the reader has never seen your project:
  - [x] One-paragraph summary of what the system does
  - [x] Setup instructions (env, dependencies, API keys) — test these yourself on a clean checkout if possible
  - [x] **Exact commands** to reproduce headline results, timed — confirm it's genuinely under 15 minutes
  - [x] Where to find: golden set, eval harness, report, decision log
  - [x] Known limitations section
- [x] Remove dead code, notebooks-only-exploration clutter from `/src`
- [x] Make sure no API keys, `.env` files, or large raw data dumps are committed
- [x] Add citations for anything borrowed (code snippets, prompt patterns, StackOverflow answers, AI-assistant-generated code you adapted) — a `CITATIONS.md` or inline comments both work
- [x] Do a final clean clone + fresh run-through of your own README to confirm reproducibility claim holds
- [x] Re-read your own code end to end once — you must be able to explain and modify it live in an interview

---

## PHASE 13 — Submission

- [ ] Confirm repo is public, or private with access granted to Hiver's recruiters
- [ ] Confirm report is included (in repo as README section or separate file, linked)
- [ ] Fill out the Notion submission form: https://intelligent-bar-256.notion.site/39492cbf0da2800682cfc78a600a745f
- [ ] Do **not** submit via email
- [ ] Double check all 5 deliverables are present: repo+README, golden set, eval harness w/ judge-agreement evidence, report (6-page equiv.), decision log

---

## Suggested Rough Timeline (10 days)
| Days | Focus |
|---|---|
| 1-2 | Phases 0-2 (setup, data, brand) |
| 2-4 | Phases 3-5 (taxonomy, prep, golden set) |
| 4-6 | Phases 6-7 (baselines, core pipeline) |
| 6-8 | Phases 8-9 (eval harness, failure analysis) |
| 8-9 | Phase 10-11 (report, decision log) |
| 9-10 | Phase 12-13 (polish, submit) |

Compress or stretch based on your actual deadline — but don't skip Phase 5 (golden set) or Phase 8's judge-agreement check to save time. Those two are the parts that separate a genuinely trustworthy submission from a plausible-looking one.
