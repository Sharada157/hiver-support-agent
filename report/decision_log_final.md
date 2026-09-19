# Final Compiled Decision Log — 15 Non-Obvious Engineering Decisions

1. **Brand Selection — Chose SpotifyCares over AppleSupport and AmazonHelp**
   - *Decision:* Selected SpotifyCares as the target brand.
   - *Reason:* Manual inspection of candidate brands revealed that AmazonHelp’s high "substantive reply" score (58/60) was inflated by mid-thread clarifying questions (e.g., *"What was advised when you contacted them?"*) and contained non-English replies. SpotifyCares had the highest volume of genuinely substantive, resolution-specific English guidance (4,081 clean customer/brand pairs).

2. **Intent Taxonomy Design — Adopted a 7-Category Taxonomy (6 Functional + Other)**
   - *Decision:* Defined 6 core functional categories (*Playback/Technical Bug, Account Access, Billing/Subscription, Content Availability, Feature Request/Complaint, Service Outage*) plus *Other*.
   - *Reason:* Validating against 80 randomly sampled customer tweets confirmed that 6 functional categories covered ~78.8% of user situations, keeping the catch-all *Other* category at 21.2% (<25% threshold) while preventing category fragmentation.

3. **Data Preprocessing — Strict English-Only Filtering**
   - *Decision:* Excluded non-English customer tweets, retaining 15,983 tweets (95.8%) out of 16,684 raw customer messages.
   - *Reason:* Taxonomy definitions, prompts, and ground truth evaluation were designed for English. Multilingual support was explicitly excluded from project scope to maximize semantic precision within the project timeline.

4. **Grounding Retrieval — Selected Local Dense Vector Embeddings (`all-MiniLM-L6-v2`)**
   - *Decision:* Built a local vector store using SentenceTransformers (`all-MiniLM-L6-v2`, 384-dim) over TF-IDF.
   - *Reason:* Dense vector embeddings capture semantic similarity (e.g., matching *"songs skipping"* with *"shuffle glitch"*) where exact keyword overlap fails, while running offline for free without external embedding API costs.

5. **Baseline Differentiation — Used TF-IDF for Simple Baseline Retrieval**
   - *Decision:* Utilized word-boundary regex rules for intent and TF-IDF cosine similarity for Simple Baseline retrieval.
   - *Reason:* Kept the Simple Baseline structurally distinct from the Full RAG Agent, establishing a clear progression between keyword matching (TF-IDF) and dense semantic vector retrieval (`all-MiniLM-L6-v2`).

6. **Dataset Integrity — Dropped Unreplied Customer Messages (17.5% of Volume)**
   - *Decision:* Dropped 866 customer tweets (17.5%) that lacked a matching brand reply.
   - *Reason:* Inferring synthetic brand replies would introduce unverified ground truth assumptions. Dropping them preserved dataset integrity, though accepted as a selection bias limitation.

7. **Multi-Provider LLM Integration — Added Groq API (`groq/compound`) Alongside Gemini and HF**
   - *Decision:* Integrated Groq API (`groq/compound`), HuggingFace Inference API, and Gemini with an environment variable switch (`LLM_PROVIDER`).
   - *Reason:* Gemini free tier rate limits (20 requests/day on 3.6 Flash) created execution bottlenecks. Groq API provided 100% free, ultra-fast inference (~500+ tokens/sec) for seamless execution.

8. **Golden Dataset Design — Stratified Sampling with Floor Minimums**
   - *Decision:* Applied stratified sampling with a minimum floor per category (min 16–33 examples per intent) for the 200-example Golden Dataset.
   - *Reason:* Pure random sampling would under-represent minority intents like *Service Outage* (8% of raw data). Stratification guaranteed statistically meaningful per-category evaluation metrics.

9. **Annotation Interface — LLM-Assisted Accept/Override Workflow**
   - *Decision:* Built an interactive labeling script showing LLM-suggested intent tags and escalation flags for human confirmation/override.
   - *Reason:* Accelerated golden set annotation speed by 4x while maintaining strict human verification for every ground truth record.

10. **Escalation Architecture — Combined Global Rules with LLM Semantic Evaluation**
    - *Decision:* Implemented both a rule-based safety guard (`decide_escalation`) and a semantic LLM evaluator (`decide_escalation_llm`).
    - *Reason:* Rule-based keywords guarantee zero-latency fail-safe escalation for legal, financial, and account compromise queries, while LLM evaluation handles complex multi-issue semantic queries.

11. **Private Account DM "Backstage" Escalation Rule**
    - *Decision:* Automatically trigger `Escalate: True` whenever a draft reply asks for private DM account details or offers to check "backstage".
    - *Reason:* Public AI agents cannot access private user account databases. Any task requiring backend account inspection must be transferred to a human agent.

12. **Confidence Calibration Cutoff at 0.90 Threshold**
    - *Decision:* Set the confidence escalation threshold to `0.90` based on Phase 8 calibration analysis.
    - *Reason:* Accuracy in the 0.70–0.80 bin was 39.1%, 0.80–0.90 was 51.0%, and 0.90–1.00 was 83.1%. The 0.90 cutoff maximized escalation recall (80.0%) for ambiguous queries.

13. **Fact Hallucination Detection without Auto-Correction Loops**
    - *Decision:* Flagged unsupported numeric facts (order IDs, dates, dollar amounts) without executing automatic prompt regeneration loops.
    - *Reason:* Automatic regeneration loops can introduce infinite execution cycles or hit API rate limits. Flagging ensures full system observability without instability.

14. **Transparent Limitation Reporting — Retained Weak Correlation Metrics**
    - *Decision:* Reported exact inter-annotator agreement (Cohen's $\kappa = 0.660$) and LLM judge-human correlation ($r = 0.353, p = 0.084$).
    - *Reason:* Retained empirical findings transparently in the report rather than re-running or cherry-picking evaluation subsets (avoiding p-hacking).

15. **Environment Variable Override Enforcement (`load_dotenv(override=True)`)**
    - *Decision:* Enabled `override=True` in `load_dotenv()`.
    - *Reason:* Guaranteed that environment settings in `.env` (`LLM_PROVIDER=groq`) always take precedence over lingering terminal environment variables in Windows PowerShell.
