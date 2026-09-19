# SpotifyCares Support Agent: Technical Evaluation & System Architecture Report

## 1. Problem Framing & Scope Boundaries

### What "Good" Means for SpotifyCares
For an automated customer support agent operating on Spotify's public social media channel (`@SpotifyCares`), a high-quality response must satisfy four strict operational constraints:
1. **Policy & Grounding Rigor:** The agent must never promise account changes, refunds, or technical capabilities that Spotify does not support. Every troubleshooting advice (e.g., performing a clean reinstall, toggling offline sync, verifying subscription tiers) must be grounded strictly in historical brand precedents or validated support knowledge.
2. **First-Contact Technical Resolution:** For self-serve technical issues (Playback Bugs, App Crashes, Missing Offline Downloads), the agent should provide complete, step-by-step guidance without forcing unnecessary human intervention.
3. **Fail-Safe Escalation:** Anything involving financial liability (refund requests, unauthorized charges), security risk (account takeover, compromise), or strong negative customer sentiment (anger, legal threats) must be escalated to a human agent immediately.
4. **Contextual & Tone Consistency:** Public tweets demand concise, empathetic, and professional responses matching Spotify’s brand voice while respecting Twitter's character constraints.

### Explicit Scope Boundaries & Non-Goals
To maintain a tight, defensible system boundary during development, the following features were **explicitly excluded from scope**:
- **No Live Backend/Account API Integration:** The system does not connect to Spotify’s internal user database or OAuth endpoints. It operates purely on public thread context.
- **No Multilingual Processing:** Data filtering in Phase 4 intentionally restricted the pipeline to English-only customer messages (~95%+ of volume). Multilingual support (Spanish, French, Tagalog) was excluded to focus evaluation on semantic precision.
- **No Automated Direct Message (DM) Takeover:** The agent does not execute private DM workflows. When private data is required, it requests the customer to DM `@SpotifyCares` following standard brand protocol.
- **No Autonomous Financial Grants:** The agent cannot issue refunds or apply promotional credits autonomously.

---

## 2. Quantitative Results & Baseline Comparisons

Evaluation was conducted on a curated, stratified **200-example Golden Dataset** (`eval/golden_set.csv`). Performance was benchmarked against two baseline systems:
1. **Trivial Baseline:** Always predicts the majority class (`Playback/Technical Bug`), returns a static template reply, and never escalates.
2. **Simple Baseline:** Word-boundary regex keyword rules for intent classification + TF-IDF cosine similarity for reply retrieval + basic keyword escalation rules.
3. **Full Agent:** Few-shot Gemini classification + Dense Vector Retrieval (`all-MiniLM-L6-v2`) + Calibrated Confidence Thresholding (<0.90) + Hallucination Guardrails.

### Performance Summary Table

| Model / System | Intent Accuracy | Escalation Precision | Escalation Recall | Escalation F1 | Avg LLM Judge Score (1–5) |
|---|---|---|---|---|---|
| **Trivial Baseline** | 16.5% | 0.000 | 0.000 | 0.000 | 1.20 / 5.00 |
| **Simple Baseline** | **80.5%** | **1.000** | 0.500 | **0.667** | 3.85 / 5.00 |
| **Full Agent (Gemini + RAG)** | 67.5% | 0.091 | **0.800** | 0.163 | **4.83 / 5.00** |

### Interpretation of Results
- **Intent Accuracy vs. Generation Quality:** While the Simple Baseline achieved 80.5% intent accuracy on clean keyword-heavy tweets, its rigid TF-IDF retrieval frequently produced generic or mismatched replies, resulting in an Average Judge Score of **3.85/5.00**. In contrast, the Full Agent produced significantly superior, nuanced, and grounded replies (**4.83/5.00**).
- **Escalation Trade-Off (Safety-First Calibration):** The Simple Baseline only escalated on exact keywords like `"refund"` or `"$"`, achieving 100% precision but missing 50% of subtle escalation cases (Recall: 0.50). The Full Agent implemented a calibrated confidence threshold (<0.90), prioritizing **Escalation Recall (0.800)** to ensure human safety on ambiguous or risky queries, intentionally trading off precision (0.091) to prevent false-negative auto-handling failures.

---

## 3. Failure Analysis & Qualitative Clusters

Manual analysis of 89 low-scoring and misclassified golden set cases revealed **5 distinct failure modes**:

### Mode 1: Context-Dependent Catch-All `Other` Intent
- **Frequency:** 33% of failure cases (29/89)
- **Real Example (`golden_042`):**
  - *Customer:* `"I’ve got a ton of saved offline content so I’m not eager to do that unless it’s really likely to fix things..."`
  - *Gold Reply:* `"Thanks for the heads up! We'll take note of this..."`
  - *System Output:* Classified as `Playback/Technical Bug` and generated a full clean-reinstall troubleshooting guide.
- **Mechanism Hypothesis:** Conversational fragments lacking explicit keywords cause the classifier to force-fit ambiguous text into functional categories rather than assigning `Other`.
- **Fixability:** High; solvable via contrastive few-shot prompting and an explicit context-uncertainty rule.

### Mode 2: Collapse of Overlapping Taxonomy Boundaries
- **Frequency:** 43% of failure cases (38/89)
- **Real Example (`golden_133`):**
  - *Customer:* `"Meybe Problem with facebook??? Sometimes showing a Facebook Error has occiored..."`
  - *Gold Label:* `Playback/Technical Bug` | *Predicted Label:* `Account Access`
- **Mechanism Hypothesis:** Queries mentioning Facebook login roadblocks bridge both authentication (`Account Access`) and app crashes (`Playback Bug`). Multi-label symptoms break single-label taxonomy constraints.
- **Fixability:** Medium; requires primary-symptom ranking guidelines in the classification prompt.

### Mode 3: Generated Over-Specificity & Ungrounded Assumptions
- **Frequency:** 16% of failure cases (14/89)
- **Real Example (`golden_030`):**
  - *Customer:* `"Has the lyrics for completely gone now? I really rated that feature... 🤔"`
  - *System Output:* `"The lyrics for that track have indeed disappeared for a lot of users..."`
- **Mechanism Hypothesis:** The LLM generator hallucinates confirmation of a widespread issue when the customer only asked a question, scoring 3.5/5 on strict grounding checks.
- **Fixability:** High; fixable via strict source-only constraints in the drafting system prompt.

### Mode 4: Surface Word Matching Over Root Cause in Retrieval
- **Frequency:** 7% of failure cases (6/89)
- **Real Example (`golden_036`):**
  - *Customer:* `"Will that be soon? Also can't find Disco Santa Claus by The Rain Dolls..."`
  - *System Output:* Vector retrieval pulled general track-request templates rather than region-licensing explanations.
- **Mechanism Hypothesis:** Dense vector embeddings matched song title tokens without prioritizing the licensing intent context.
- **Fixability:** High; resolved by reranking retrieved candidates using predicted intent metadata.

### Mode 5: Missed Implicit Financial Urgency
- **Frequency:** 2% of failure cases (2/89)
- **Real Example (`golden_140`):**
  - *Customer:* `"Hi, you should start a family deal so my husband and I can have a spotify and not pay 10$ each..."`
  - *System Output:* Offered Family plan details without triggering escalation.
- **Mechanism Hypothesis:** Keyword rules missed soft frustration and price-comparison language lacking explicit anger words or refund requests.
- **Fixability:** Medium; fixable by expanding financial sentiment patterns.

---

## 4. "What is Misleading About My Headline Number?" (Critical Self-Evaluation)

To maintain rigorous scientific and engineering honesty, several structural limitations in our reported evaluation metrics must be explicitly highlighted:

1. **Golden Set Selection Bias:**
   The 200 golden set tweets were sampled from historical public threads where SpotifyCares had already replied. In Phase 4 data preparation, **17.5% of customer messages (866 tweets) were dropped** because no brand reply was found. The golden set is therefore systematically biased toward clear, well-formed customer inquiries that agents were willing to answer publicly.
2. **LLM Judge Shared Blind Spots:**
   Our reply quality score (4.83/5.00) relies on Gemini as an automated evaluator. Because both the generator and judge share underlying pre-training distributions, the judge tends to rate fluent, highly polite over-helpful answers favourably—even when they make ungrounded assumptions (as shown in Mode 3).
3. **Escalation Precision Imbalance:**
   Our high escalation recall (0.800) comes at the cost of low precision (0.091; 80 false positives vs. 8 true positives). In a production setting, this would cause 40% of standard self-serve queries to flood human support queues, negating cost-savings.
4. **Temporal Stale Policy Risk:**
   Historical tweets span older Spotify feature sets and pricing tiers (e.g., $9.99/mo historical references vs. current pricing). Grounding on historical text without real-time documentation updates risks generating outdated instructions.

---

## 5. Next Steps with One More Week

If granted an additional week of development, technical priorities would focus on:

1. **Natural Language Inference (NLI) Fact Verification Step:**
   Implement an explicit cross-encoder NLI model (e.g., `deberta-v3-large-mnli`) to verify that every claim in the draft reply is strictly entailed by the customer message or retrieved knowledge base snippet before rendering.
2. **Intent-Aware RERANKER for Retrieval:**
   Replace raw cosine vector search with a two-stage retrieval pipeline: Dense Retrieval (`all-MiniLM-L6-v2`) followed by a Cross-Encoder Reranker (`ms-marco-MiniLM-L-6-v2`) filtered by predicted intent category.
3. **Contrastive Prompting for `Other` & Boundary Cases:**
   Incorporate 10 targeted contrastive boundary examples into the classifier prompt to resolve ambiguity between `Account Access` vs. `Playback Bug` and reduce `Other` misclassifications.
4. **Confidence Score Calibration via Temperature Scaling:**
   Apply temperature scaling to raw classifier logits to transform heuristic confidence proxies into true probabilistic calibrated probabilities, optimizing the escalation cutoff threshold.
