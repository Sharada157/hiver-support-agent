# SpotifyCares AI Support Agent

An intelligent, grounded AI customer support agent built for Spotify's public social media channel (`@SpotifyCares`) using the *Customer Support on Twitter* dataset. 

The system classifies customer tweets into a 7-category intent taxonomy, drafts grounded support responses using dense vector retrieval (RAG) over ~4,000 real historical Spotify resolutions, detects ungrounded hallucinated facts, and enforces a safety-first escalation policy to human agents.

---

## 🚀 Quick Summary
- **Intent Classification:** 7 categories (*Playback Bug, Account Access, Billing/Subscription, Content Availability, Feature Request, Service Outage, Other*) using few-shot LLM prompting.
- **Grounding (RAG):** Dense vector retrieval (`all-MiniLM-L6-v2`) over 4,081 clean Spotify support resolution pairs.
- **Fail-Safe Escalation:** Hybrid rule guard + LLM policy evaluator (`decide_escalation_llm`) covering financial liabilities, account lockouts, anger/threats, and private DM "backstage" account lookups.
- **Empirical Evaluation:** Evaluated on a hand-labeled 200-example Golden Dataset (`eval/golden_set.csv`) against Trivial and Simple Keyword+TF-IDF baselines.

---

## 🛠️ Setup (Under 5 Minutes)

### 1. Clone Repository & Navigate
```bash
git clone https://github.com/Sharada157/hiver-support-agent.git
cd hiver-support-agent
```

### 2. Set Up Virtual Environment & Dependencies
```powershell
# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure API Credentials (`.env`)
Create a `.env` file in the project root:
```env
# Primary Fast Provider (Groq API - Free key at: https://console.groq.com/keys)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=groq/compound

# Optional Backup Providers
GEMINI_API_KEY=your_gemini_api_key_here
HF_TOKEN=your_huggingface_token_here
```

---

## ⚡ Quick Demo (10 Seconds)

Run a test query through the end-to-end agent pipeline:

```powershell
python src/demo.py
```

### Example Output
```text
============================================================
INPUT: I am writing to get help with a login issue on my account. I am currently locked out and unable to access my profile, but my payment method is still being charged for a Premium subscription.
============================================================
Predicted Intent: Account Access
Confidence: 1.0

Drafted Reply: Hey there! Help's here. Could you send us a DM with your account's email address or username? We'll take a look backstage to see what's going on /AB

Escalate: True
Reason: Financial liability or billing concern detected — requires human verification

Hallucination flagged: False
```

---

## 📊 Reproduce Headline Evaluation Results

Execute the reproduction pipeline in sequence:

```powershell
# 1. Build Knowledge Base & Embeddings (~2 min)
python notebooks/04_data_preparation.py

# 2. Run Trivial & Simple Baselines (~1 min)
python eval/run_baselines.py

# 3. Run Full RAG Agent Pipeline (~2 min)
python src/run_pipeline.py

# 4. Generate Comparative Metrics & Failure Analysis
python eval/phase9_analysis.py
```

### Headline Results Comparison

| System / Model | Intent Accuracy | Escalation Precision | Escalation Recall | Escalation F1 | Avg LLM Judge Score (1–5) |
|---|---|---|---|---|---|
| **Trivial Baseline** | 16.5% | 0.000 | 0.000 | 0.000 | 1.20 / 5.00 |
| **Simple Baseline (Regex+TF-IDF)** | **80.5%** | **1.000** | 0.500 | **0.667** | 3.85 / 5.00 |
| **Full Agent (RAG + Guardrails)** | 67.5% | 0.091 | **0.800** | 0.163 | **4.83 / 5.00** |

---

## 📁 Repository Structure

```text
hiver-support-agent/
├── data/
│   ├── raw/                        # Raw Twitter support dataset
│   └── processed/                  # Cleaned triples, knowledge base, & embeddings (.npy)
├── src/
│   ├── pipeline.py                 # Core RAG Agent, classifier, & escalation engine
│   ├── baselines.py                # Trivial & Simple baseline implementations
│   ├── run_pipeline.py             # Agent evaluation execution script
│   └── demo.py                     # Interactive CLI demonstration script
├── eval/
│   ├── golden_set.csv              # Stratified 200-example ground-truth dataset
│   ├── phase9_analysis.py          # Failure mode clustering & bias evaluation
│   ├── harness.py                  # Pipeline execution harness
│   └── judge.py                    # LLM-as-a-Judge scoring module
├── report/
│   ├── report.md                   # Comprehensive Final Technical Synthesis Report
│   ├── failure_modes.md            # Deep-dive analysis of 5 failure modes
│   ├── decision_log_final.md       # Compiled list of 15 non-obvious engineering decisions
│   ├── decision_log.md             # Development decision journal
│   └── taxonomy_final.md           # 7-Category Intent Taxonomy specification
├── .env                            # Environment variable configuration
├── requirements.txt                # Python package dependencies
├── CITATIONS.md                    # Project citations & references
└── README.md                       # Project overview & reproduction guide
```

---

## 📌 Key Deliverables

- **Final Technical Synthesis Report:** [`report/report.md`](file:///c:/Users/Vishal%20Naidu/OneDrive/Desktop/Deep_learning/hiver-support-agent/report/report.md)
- **Failure Analysis Document:** [`report/failure_modes.md`](file:///c:/Users/Vishal%20Naidu/OneDrive/Desktop/Deep_learning/hiver-support-agent/report/failure_modes.md)
- **Final Decision Log (15 Decisions):** [`report/decision_log_final.md`](file:///c:/Users/Vishal%20Naidu/OneDrive/Desktop/Deep_learning/hiver-support-agent/report/decision_log_final.md)
- **200-Example Golden Dataset:** [`eval/golden_set.csv`](file:///c:/Users/Vishal%20Naidu/OneDrive/Desktop/Deep_learning/hiver-support-agent/eval/golden_set.csv)

---

## ⚠️ Known Limitations

1. **Knowledge Base Selection Bias:** 17.5% of raw customer tweets (866 messages) lacked brand replies and were dropped. The system only learns from issues Spotify resolved publicly.
2. **Escalation Precision Imbalance:** Prioritizing high escalation recall (0.800) yields low precision (0.091), escalating ~40% of queries to human queues to guarantee safety.
3. **Temporal Policy Decay:** Historical tweets reflect older Spotify feature sets and pricing tiers (e.g., $9.99/mo historical references vs. current pricing).
4. **LLM Judge Shared Blind Spots:** Evaluator LLM shares pre-training distributions with the generator, occasionally rating fluent over-helpful responses favorably.

---

## 📜 Citations
See [`CITATIONS.md`](file:///c:/Users/Vishal%20Naidu/OneDrive/Desktop/Deep_learning/hiver-support-agent/CITATIONS.md) for full dataset, model, and software library references.