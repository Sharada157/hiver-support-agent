# Golden Set: Sampling & Labeling Methodology

**Sampling:** Stratified by intent with a target minimum per category, drawn
from SpotifyCares customer messages that received a brand reply. Excluded all
examples previously seen during Phase 3 taxonomy design (confirmed 0 overlap).

**Final set:** 200 examples across 7 intent categories (16-33 per class).

**Labeling:** Performed personally, following the rubric in `labeling_guide.md`.
Each example labeled for intent, a reference reply/key-facts, and an
escalate/auto-handle decision with stated reason.

**Golden-set label agreement:** A blind 25-example subset was independently
re-labeled in a second pass. Results: intent agreement = 72.00%, kappa = 0.660;
escalation agreement = 96.00%, kappa = 0.648.

**Reply-quality judge agreement:** Separately, LLM-judge reply-grounding scores
were checked against human scoring on a 25-example subset (see
`judge_agreement_sample.csv`), Spearman correlation = 0.353 (p = 0.08365).
