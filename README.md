# hiver-support-agent


# Hiver SDE Intern Assignment — Progress Log

**Project:** AI Support Agent for SpotifyCares (Twitter Customer Support dataset)
**Status as of this log:** Phases 0-7 complete

---

## PHASE 0 — Environment & Project Setup ✅ COMPLETE

- GitHub repo created: `hiver-support-agent`, public, with Python `.gitignore` + license
- Virtual environment (`venv`) set up, working on both Ubuntu server and Windows laptop (later migrated to laptop via `git clone`)
- Folder structure established:
  ```
  /data/raw, /data/processed
  /notebooks
  /src
  /eval
  /report
  /outputs/runs, /outputs/baselines
  ```
- **LLM provider decision: Google Gemini** (via `google-genai` SDK), chosen over Claude/DeepSeek/Hermes for:
  - Genuine free tier, no payment method required (removes reviewer reproducibility friction)
  - Simple setup vs. Hermes (requires GPU hosting or paid API access through third parties)
  - Better reported tone/nuance than DeepSeek for reply drafting
- `.env` set up with `GEMINI_API_KEY` and later `HF_TOKEN` (for Hugging Face model downloads)
- **Security incident:** API key was accidentally exposed in terminal screenshots twice; both times flagged and rotated
- `src/config.py` created with `set_seed()` for reproducibility (seed = 42 used throughout)
- `requirements.txt` maintained incrementally: `google-genai`, `python-dotenv`, `pandas`, `numpy`, `sentence-transformers`, `scikit-learn`, `scipy`

---

## PHASE 1 — Data Acquisition & Exploration ✅ COMPLETE

**File:** `notebooks/01_explore.py`

- Downloaded Kaggle "Customer Support on Twitter" dataset (`thoughtvector/customer-support-on-twitter`)
- Actual file location: `data/raw/twcs/twcs.csv` (not flat `data/raw/twcs.csv` — corrected path issue)
- Loaded into pandas, checked shape, nulls, duplicates
- Built `build_thread(df, tweet_id)` function: walks backward to conversation root via `in_response_to_tweet_id`, then forward through all `response_tweet_id` chains (handles comma-separated multi-reply IDs)
- Identified customer vs. brand messages via `author_id` pattern (brand = readable name, customer = numeric/anonymized)
- Checked timestamp range of dataset (confirmed dataset is from ~2015-2017 — noted as a report limitation: brand policies/product features may have changed significantly since)
- Got brand volume rankings via `author_id` non-numeric filtering

---

## PHASE 2 — Brand Selection & Validation ✅ COMPLETE

**File:** `notebooks/02_brand_validation.py`

- Shortlisted 3 candidates: SpotifyCares, AppleSupport, AmazonHelp
- **Round 1 (keyword heuristic, n=40 per brand):** SpotifyCares 28 substantive/12 generic-DM-redirect; AppleSupport 27/13; AmazonHelp 40/0 (flagged as suspicious)
- **Round 2 (refined 3-category classification, n=60 per brand):** SpotifyCares 41 substantive/18 generic/1 closing; AppleSupport 37/23/0; AmazonHelp 58/1/1
- **Critical finding:** AmazonHelp's high "substantive" score was an artifact — manual inspection showed most were mid-thread clarifying questions ("What was advised when you contacted them?"), not real resolutions. Amazon's data also contained non-English replies (French observed).
- **Final decision: SpotifyCares** — most genuinely substantive, resolution-specific content on manual review; consistent English; recurring, learnable resolution patterns (e.g., restart/update advice for playback bugs)
- Full brand replies + customer tweets filtered and reconstructed into multi-turn threads (2,000-thread sample), saved to `data/raw/spotify_full_threads.csv`
- Decision fully documented in `report/decision_log.md`

---

## PHASE 3 — Intent Taxonomy Design & Validation ✅ COMPLETE

**Files:** `notebooks/03_taxonomy_design.py`, `report/taxonomy_final.md`, `report/taxonomy_draft_v1.md`, `report/taxonomy_ambiguous_cases.md`

- Drafted initial 7-category taxonomy (6 real + "Other") based on prior knowledge
- Validated against 80 randomly sampled real customer tweets, manually labeled by hand
- Checked "Other" percentage, checked for category overlap/ambiguity
- **Finalized taxonomy (7 categories):**
  1. Playback/Technical Bug
  2. Account Access
  3. Billing/Subscription
  4. Content Availability
  5. Feature Request/Complaint
  6. Service Outage
  7. Other
- Drafted escalation rules (v1): refund/dollar mentions, account compromise language, anger/threat keywords, low confidence (threshold TBD), repeat contact
- All decisions and edge cases logged in `report/decision_log.md`

---

## PHASE 4 — Data Preparation Pipeline ✅ COMPLETE

**File:** `notebooks/04_data_preparation.py`

**Cleaning:**
- Stripped URLs and @mentions, preserved original raw text in a separate column
- Kept emojis (potential sentiment signal for escalation), documented decision
- Language detection via `langdetect`: 15,983 English out of ~16,700+ total; filtered to English-only (documented as an explicit scope limitation — no multilingual support)

**Deduplication:**
- Removed 6,468 exact duplicate rows
- Removed 7 additional near-duplicate rows (normalized-template matching)

**Triple construction (customer_message, brand_reply, thread_context):**
- Total customer messages seen: 4,947
- Kept (had a matching brand reply): 4,081
- Dropped (no brand reply found): 866 (17.5%) — **documented as a real selection-bias limitation**: system only learns from publicly-answered issues, not DM-only or unanswered ones

**Knowledge base for grounding:**
- Final size: 4,081 (customer_message, brand_reply) pairs
- **Retrieval method decision: local embeddings** (sentence-transformers `all-MiniLM-L6-v2`, 384-dim) over TF-IDF or hosted embedding APIs — chosen for semantic matching quality, zero API cost, full reviewer reproducibility using local GPU
- Saved: `data/processed/spotify_triples.csv`, `data/processed/knowledge_base.csv`, `data/processed/kb_embeddings.npy`

---

## PHASE 5 — Golden Evaluation Set Creation ✅ COMPLETE

**Files:** `eval/golden_set.csv`, `eval/labeling_guide.md`, `eval/sampling_and_labeling_note.md`, `eval/label_agreement_blind.csv`, `eval/judge_agreement_sample.csv`

**Sampling:**
- Stratified by intent, target minimum ~20 per class, LLM-assisted rough-tagging used only to guide sampling (not as final labels)
- Excluded all examples seen during Phase 3 taxonomy design — **confirmed 0 overlap**

**Final golden set — verified:**
- 200 rows, 0 duplicate IDs, 0 duplicate texts, 0 missing values
- Columns: `id, text, thread_context, gold_intent, gold_reply_reference, gold_escalate, gold_escalate_reason` (plus `actual_historical_reply` extra)
- Intent distribution: Playback/Technical Bug 33, Content Availability 32, Feature Request/Complaint 32, Billing/Subscription 30, Other 29, Account Access 28, Service Outage 16
- 10 escalation-positive cases

**Labeling method:**
- Hand-labeled with an accept/override interface (suggested intent + suggested escalation shown, human confirms or corrects every single example — documented explicitly as an assisted-but-human-verified process)

**Golden-set label agreement (second-pass, 25-example blind subset):**
- Intent: 72.00% agreement, Cohen's kappa = 0.660
- Escalation: 96.00% agreement, Cohen's kappa = 0.648

**Judge-human agreement (reply quality, separate check):**
- Spearman correlation = 0.353, p = 0.084 — **weak and not statistically significant**, documented honestly as a limitation (small sample size, possible scoring inconsistency)

**Cleanup:** intermediate/scratch files (`golden_set_bot_progress.csv`, `golden_set_in_progress.csv`, `golden_set_manual.csv`, `golden_set_review.csv`) moved to `eval/scratch/`

---

## PHASE 6 — Baseline Systems ✅ COMPLETE

**Files:** `src/baselines.py`, `eval/run_baselines.py`, `outputs/baselines/`

**Trivial baseline:** always predicts most frequent intent (Playback/Technical Bug), fixed generic reply, never escalates
- Intent accuracy: **16.50%**
- Escalation: 0% precision/recall/F1 (as expected — never escalates)

**Simple baseline:** word-boundary regex keyword rules for intent; TF-IDF cosine similarity for nearest-neighbor reply retrieval from knowledge base; escalates only on explicit refund/dollar keywords
- Intent accuracy: **80.50%**
- Escalation: 100% precision, 50% recall, 66.67% F1
- Per-category: strong on Account Access (96.4%), Service Outage (100%), Other (96.5%); weaker on Billing/Subscription (46.7%), Playback/Technical Bug (66.7% — dropped after regex tightening, a documented, explainable brittleness of keyword rules)

**Process note (documented honestly):** baselines were built partly alongside early full-agent work rather than strictly beforehand, and the simple baseline's retrieval method was upgraded mid-development from crude word-overlap to proper TF-IDF. Baseline logic was not tuned based on full-agent results.

Predictions and metrics saved to `outputs/baselines/`.

---

## PHASE 7 — Core Agent Pipeline ✅ COMPLETE

**Files:** `src/pipeline.py`, `src/run_pipeline.py`, `notebooks/06_confidence_calibration.py`, `report/confidence_calibration.png`

**What's built:**
- `classify_intent_with_confidence(text)` — LLM (Gemini) few-shot classification with validated confidence parsing and fallback to `Other`
- `call_gemini_with_retry(prompt)` — retry-with-backoff wrapper for API rate limits (fixed a critical earlier bug where silent fallback made the "full agent" secretly run baseline logic)
- `retrieve_similar(text, top_k=3)` — embedding-based nearest-neighbor retrieval from knowledge base
- `draft_reply(text, thread_context, retrieved_examples)` — grounded reply generation using retrieved historical examples
- `check_for_hallucinated_facts(...)` — flags unsupported dollar amounts, dates, and long numeric identifiers
- `decide_escalation(...)` — keyword, confidence, fallback, and repeat-contact escalation rules
- `run_agent(text, thread_context, num_turns=1)` — wires all steps together and returns structured logs

**⚠️ Known issue found and partially fixed:** An early full-agent evaluation run showed intent predictions identical to the simple baseline for nearly all 200 examples — traced to a silent fallback swallowing API errors. Fixed by switching to `gemini-2.5-flash` (higher free-tier quota) and adding explicit retry/backoff with loud failure instead of silent fallback.

**Phase 7 full run (200-example golden set):**
- Intent accuracy: **67.5%**
- Confidence calibration: 83.1% accuracy in the 0.9-1.0 bin versus 51.0% in the 0.8-0.9 bin; threshold set to **0.90**
- Classification fallbacks: **0**; hallucination flags: **1**
- Full JSON and flat CSV logs saved under `outputs/runs/`; calibration plot saved to `report/confidence_calibration.png`

**Phase 9 update:** After the few-shot and confidence changes, `Other` accuracy is 31.0% and `Content Availability` is 43.8%, the weakest functional category. The failure analysis confirms that short conversational context and neighboring taxonomy boundaries remain the main intent risks. Detailed cases are in `eval/results/worst_cases_raw.csv` and `report/failure_modes.md`.

**Completed Phase 7 deliverables:**
- [x] Few-shot classification, fallback, hallucination flagging, retrieved-example logging
- [x] Confidence and repeat-contact escalation
- [x] Calibration plot and threshold decision
- [x] Small 8-example test batch and full 200-example run
- [x] Decision log and reproducible output artifacts

---

## PHASES NOT YET STARTED

- **Phase 8 — Evaluation Harness:** partially exists (`eval/harness.py`, `eval/judge.py`, `eval/postprocess.py` built and used to generate the Phase 6/7 numbers above), but needs final consolidation once Phase 7 fixes land, plus LLM-judge reply-grounding score already computed (avg 4.83/5 on a 60-example subsample — **this number should be treated cautiously given the weak judge-human correlation noted in Phase 5**)
- **Phase 9 — Failure Analysis:** complete. Ranked 89-row failure union, manually reviewed notes, five failure modes, bias slices, and dialect/sarcasm check are saved in `eval/results/` and `report/failure_modes.md`. The Phase 8-equivalent source artifacts are under `outputs/runs/` in this checkout; the spec-named `eval/results/judge_scores_agent.csv` and `intent_metrics_agent.json` were not present.
- **Phase 10 — Report Writing:** not started
- **Phase 11 — Decision Log:** ongoing throughout (entries added incrementally in `report/decision_log.md`), needs final compilation/cleanup pass
- **Phase 12 — Repo Polish & Reproducibility:** not started
- **Phase 13 — Submission:** not started

---

## Known Open Issues / Things to Revisit

1. Weak, non-significant judge-human correlation (0.353, p=0.084) — needs honest treatment in the report, not a fixed problem
2. LLM agent underperforms simple baseline on overall intent accuracy (70.5% vs 80.5%) — real, investigated finding, not yet fully written up
3. "Other" category is the single biggest weak point in the full agent (20.7% accuracy) — root cause hypothesized (LLM reluctance to pick vague catch-all) but not yet confirmed via few-shot example fix
4. Reply grounding judge score (4.83/5) was only computed on a 60-example subsample (not all 200) to conserve API quota — documented, but should be flagged again in the report
5. Confidence threshold for escalation is currently a guess (~0.6), not yet empirically calibrated
6. Phase 6 baselines were built partly out of the assignment's recommended order (alongside early agent work, not strictly before) — documented honestly, not hidden

---

## Repository Structure (current)

```
hiver-support-agent/
├── data/
│   ├── raw/twcs/twcs.csv, spotify_full_threads.csv
│   └── processed/spotify_triples.csv, knowledge_base.csv, kb_embeddings.npy
├── notebooks/
│   ├── 01_explore.py
│   ├── 02_brand_validation.py
│   ├── 03_taxonomy_design.py
│   ├── 04_data_preparation.py
│   ├── 05_golden_set_creation.py
│   └── 06_confidence_calibration.py (planned)
├── src/
│   ├── config.py
│   ├── baselines.py
│   ├── pipeline.py
│   └── run_pipeline.py
├── eval/
│   ├── golden_set.csv
│   ├── labeling_guide.md
│   ├── sampling_and_labeling_note.md
│   ├── label_agreement_blind.csv
│   ├── judge_agreement_sample.csv
│   ├── harness.py
│   ├── judge.py
│   ├── postprocess.py
│   ├── run_baselines.py
│   └── scratch/ (intermediate files)
├── outputs/
│   ├── baselines/ (trivial + simple baseline predictions & metrics)
│   └── runs/ (full agent predictions, judge scores, failure examples)
├── report/
│   ├── decision_log.md
│   ├── taxonomy_final.md
│   ├── taxonomy_draft_v1.md
│   └── taxonomy_ambiguous_cases.md
├── requirements.txt
└── README.md (not yet finalized)
```