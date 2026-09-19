# Project Citations & Dependencies

## 1. Primary Dataset
- **Dataset Title:** Customer Support on Twitter
- **Source:** Kaggle (`thoughtvector/customer-support-on-twitter`)
- **License:** Public Domain / Open Dataset
- **Usage:** Preprocessed and filtered to SpotifyCares support threads (`data/processed/spotify_triples.csv`).

## 2. Pretrained Machine Learning Models
- **Sentence Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face)
  - *Reference:* Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP*.
  - *Usage:* Dense vector embedding generation for knowledge base retrieval grounding (`data/processed/kb_embeddings.npy`).

- **Large Language Model Inference APIs:**
  - **Groq LPU Inference API:** `groq/compound` (Groq Cloud)
  - **Google Gemini API:** `gemini-2.5-flash` / `gemini-3.6-flash` (Google AI Studio)
  - **Hugging Face Inference API:** `Qwen/Qwen2.5-7B-Instruct` (Hugging Face Hub)

## 3. Core Software Libraries & Frameworks
- **Data Processing & Vector Operations:** `pandas` (v2.x), `numpy` (v1.26+), `scikit-learn` (v1.3+)
- **Embedding & RAG Pipeline:** `sentence-transformers`, `huggingface-hub`, `httpx`
- **LLM SDKs:** `google-genai`, `python-dotenv`

## 4. Architectural Patterns & Heuristics
- **Classification Method:** Few-shot in-context learning with calibrated confidence proxies.
- **Escalation Architecture:** Hybrid rule-based safety guard + LLM semantic policy evaluation.
- **Hallucination Checking:** Regex-based numeric & entity extraction matching against source context.
