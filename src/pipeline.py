import os
import re
import time
import numpy as np
import pandas as pd
import httpx
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from google import genai
from huggingface_hub import InferenceClient

load_dotenv()
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN", "")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
if LLM_PROVIDER == "hf":
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise RuntimeError("LLM_PROVIDER=hf requires HF_TOKEN to be set in the environment.")
    llm_client = InferenceClient(model=HF_MODEL, token=HF_TOKEN)
elif LLM_PROVIDER == "ollama":
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    if not OLLAMA_API_KEY:
        raise RuntimeError("LLM_PROVIDER=ollama requires OLLAMA_API_KEY to be set in the environment.")
    llm_client = None
else:
    llm_client = genai.Client()
embedder = SentenceTransformer('all-MiniLM-L6-v2')
API_AVAILABLE = True

knowledge_base = pd.read_csv("data/processed/knowledge_base.csv")
kb_embeddings = np.load("data/processed/kb_embeddings.npy")

TAXONOMY_WITH_EXAMPLES = """
1. Playback/Technical Bug - app crashes, skipping, freezing, broken features
    Example: "Everything else works, it's just that the music won't play."

2. Account Access - login, password, 2FA, lockout issues
    Example: "Deactivated Facebook and cannot log on to Spotify."

3. Billing/Subscription - charges, refunds, plan/subscription issues
    Example: "You charged me twice for my service this month."

4. Content Availability - missing songs/podcasts, licensing/region issues
    Example: "This album is not available on Spotify."

5. Feature Request/Complaint - wants a feature, dislikes a product decision
    Example: "I really want to be able to delete radio stations from my recently played."

6. Service Outage - widespread known issue, or users ask whether Spotify is down
    Example: "Is Spotify down or is my phone being stupid?"

7. Other - praise, spam, ambiguous, off-topic, or conversational messages
    Example: "DM sent, thanks."
"""

INTENTS = {
     "Playback/Technical Bug",
     "Account Access",
     "Billing/Subscription",
     "Content Availability",
     "Feature Request/Complaint",
     "Service Outage",
     "Other",
}


def call_llm_with_retry(prompt, max_retries=5):
    """Call the selected provider with bounded retries and no silent fallback."""
    for attempt in range(max_retries):
        try:
            if LLM_PROVIDER == "hf":
                response = llm_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=int(os.getenv("HF_MAX_TOKENS", "512")),
                )
                return response.choices[0].message.content.strip()
            if LLM_PROVIDER == "ollama":
                response = httpx.post(
                    f"{OLLAMA_BASE_URL}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0,
                    },
                    timeout=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")),
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()
            response = llm_client.interactions.create(model=GEMINI_MODEL, input=prompt)
            return response.output_text.strip()
        except Exception as error:
            error_text = str(error).lower()
            if LLM_PROVIDER == "hf" and ("403" in error_text or "forbidden" in error_text):
                raise RuntimeError(
                    "Hugging Face rejected the request (403). Create a token with "
                    "Inference Providers permission, enable provider access/credits, "
                    "and set it as HF_TOKEN."
                ) from error
            if LLM_PROVIDER == "hf" and ("401" in error_text or "unauthorized" in error_text):
                raise RuntimeError(
                    "Hugging Face rejected HF_TOKEN (401). Create a new valid token "
                    "and set it in the environment."
                ) from error
            if LLM_PROVIDER == "ollama" and ("401" in error_text or "403" in error_text or "unauthorized" in error_text or "forbidden" in error_text):
                raise RuntimeError(
                    "Ollama Cloud rejected OLLAMA_API_KEY. Create a new valid key, "
                    "ensure it has cloud inference access, and update .env."
                ) from error
            is_rate_limited = "429" in error_text or "quota" in error_text or "rate limit" in error_text
            if not is_rate_limited:
                raise
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"{LLM_PROVIDER} quota/rate limit persisted after retries; stopping instead of using a fallback."
                ) from error
            wait_time = int(os.getenv("LLM_RETRY_SECONDS", "15")) * (attempt + 1)
            print(f"{LLM_PROVIDER} rate limited; waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait_time)

def classify_intent_with_confidence(text):
    prompt = f"""Classify this customer support tweet into exactly one category, using the examples as a guide.

{TAXONOMY_WITH_EXAMPLES}

Tweet to classify: "{text}"

Respond in exactly this format:
Category: <category name>
Confidence: <number from 0.0 to 1.0>"""
    try:
        raw = call_llm_with_retry(prompt)
    except Exception as error:
        print(f"WARNING: classification failed for {str(text)[:50]}... defaulting to Other")
        return "Other", 0.0, True

    category = "Other"
    confidence = 0.0
    for line in raw.splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue
        if key.strip().lower() == "category":
            category = value.strip()
        elif key.strip().lower() == "confidence":
            try:
                confidence = float(value.strip())
            except ValueError:
                confidence = 0.0

    if category not in INTENTS:
        category = "Other"
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    return category, confidence, False


def classify_intent(text):
    """Return only the validated category for legacy callers."""
    intent, _, _ = classify_intent_with_confidence(text)
    return intent

def retrieve_similar(text, top_k=3):
    query_emb = embedder.encode([text])[0]
    sims = kb_embeddings @ query_emb / (
        np.linalg.norm(kb_embeddings, axis=1) * np.linalg.norm(query_emb) + 1e-8
    )
    top_idx = np.argsort(sims)[-top_k:][::-1]
    return knowledge_base.iloc[top_idx][['customer_message', 'brand_reply']].to_dict('records')

def draft_reply(text, thread_context, retrieved_examples):
    examples_text = "\n".join(
        f"- Customer: {ex['customer_message']}\n  Reply: {ex['brand_reply']}"
        for ex in retrieved_examples
    )
    prompt = f"""You are a SpotifyCares support agent. Write a short, helpful reply
to the customer's message, in a tone consistent with these real past examples.
Do NOT invent specific facts (order numbers, dates, amounts) not present in the input.

Past similar cases:
{examples_text}

Thread context: {thread_context}
Customer message: {text}

Reply:"""
    return call_llm_with_retry(prompt)

def check_for_hallucinated_facts(generated_reply, text, thread_context, retrieved_examples):
    """Flag specific numeric facts that are not present in available source text."""
    source_text = " ".join([
        str(text),
        str(thread_context),
        *[
            f"{example['customer_message']} {example['brand_reply']}"
            for example in retrieved_examples
        ],
    ])
    fact_pattern = r"\$\d+(?:\.\d{2})?|\b\d{4,}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b"
    reply_facts = re.findall(fact_pattern, str(generated_reply))
    source_facts = set(re.findall(fact_pattern, source_text))
    unsupported = [fact for fact in reply_facts if fact not in source_facts]
    return {
        "flagged": bool(unsupported),
        "unsupported_facts": unsupported,
    }


def decide_escalation(
    text,
    intent,
    confidence=0.0,
    thread_context="",
    num_turns=1,
    confidence_threshold=0.9,
    reply="",
):
    text_lower = str(text).lower()
    reply_lower = str(reply).lower()

    if any(kw in text_lower for kw in ["refund", "$", "charge", "charged", "statement", "bank", "card", "billing", "payment"]):
        return True, "Financial liability or billing concern detected — requires human verification"
    if intent == "Account Access" and any(kw in text_lower for kw in ["hacked", "unauthorized", "not me", "locked out", "login issue", "unable to access", "access my profile"]):
        return True, "Possible account compromise or lockout — needs human verification"
    backstage_keywords = ["backstage", "under the hood", "behind the scenes", "dm us your", "send us a dm", "dm us the email", "account's email"]
    if any(kw in reply_lower for kw in backstage_keywords) or any(kw in text_lower for kw in backstage_keywords):
        return True, "Private account lookup or 'backstage' inspection required — escalating to human agent"
    if any(kw in text_lower for kw in ["lawyer", "cancelling", "furious", "unacceptable"]):
        return True, "Anger/threat language detected"
    if confidence < confidence_threshold:
        return True, f"Low classifier confidence ({confidence:.2f}), below threshold ({confidence_threshold:.2f})"
    if num_turns >= 4:
        return True, f"Repeat contact - {num_turns} turns in thread without apparent resolution"
    return False, "No escalation trigger matched"


def run_agent(text, thread_context="", num_turns=1):
    start_time = time.perf_counter()
    intent, confidence, intent_fallback = classify_intent_with_confidence(text)
    retrieved = retrieve_similar(text)
    reply = draft_reply(text, thread_context, retrieved)
    hallucination_check = check_for_hallucinated_facts(
        reply, text, thread_context, retrieved
    )
    escalate, reason = decide_escalation(
        text,
        intent,
        confidence,
        thread_context,
        num_turns,
        reply=reply,
    )
    return {
        "input_text": text,
        "thread_context": thread_context,
        "intent": intent,
        "confidence": confidence,
        "intent_used_fallback": intent_fallback,
        "num_turns": num_turns,
        "reply": reply,
        "hallucination_flagged": hallucination_check["flagged"],
        "hallucination_details": hallucination_check["unsupported_facts"],
        "escalate": escalate,
        "escalate_reason": reason,
        "retrieved_examples": retrieved,
        "latency_seconds": round(time.perf_counter() - start_time, 2),
    }