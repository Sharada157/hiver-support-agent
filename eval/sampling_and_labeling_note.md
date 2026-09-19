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




**Note on judge-human correlation:** The correlation (0.353, p=0.084) is weak 
and not statistically significant at conventional thresholds, likely due to 
the small sample size (25 examples) and possible inconsistency in how the 
human scorer applied the 1-5 rubric across sittings. This is flagged 
explicitly rather than treated as a passing check — it means the LLM judge's 
reply-quality scores should be treated as a rough signal, not a precise 
metric, until a larger or more carefully controlled agreement study is done.
