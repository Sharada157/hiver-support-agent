import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

INTENTS = [
    "Playback/Technical Bug", "Account Access", "Billing/Subscription",
    "Content Availability", "Feature Request/Complaint", "Service Outage", "Other"
]

# ---- Trivial baseline ----
def trivial_predict(text, thread_context=""):
    return {
        "intent": "Playback/Technical Bug",  # most frequent class, hardcoded
        "reply": "Thanks for reaching out! Please DM us so we can look into this.",
        "escalate": False,
        "escalate_reason": "Trivial baseline never escalates"
    }

# ---- Simple baseline: keyword rules + nearest-neighbor reply ----
KEYWORD_RULES = [
    ("Service Outage", (r"\bdown\b", r"\boutage\b", r"\bserver\b")),
    ("Account Access", (r"\blogin\b", r"\blog in\b", r"\bpassword\b", r"\b2fa\b", r"\blocked out\b")),
    ("Billing/Subscription", (r"\bcharge\b", r"\bcharged\b", r"\brefund\b", r"\bsubscription\b", r"\bbilling\b")),
    ("Content Availability", (r"\bmissing\b", r"\bunavailable\b", r"\bremoved\b", r"\bregion\b")),
    ("Feature Request/Complaint", (r"\bplease add\b", r"\bwish\b", r"\bfeature\b", r"\bwhy did you remove\b")),
    ("Playback/Technical Bug", (r"\bcrash\b", r"\bskip\b", r"\bfreeze\b", r"\bbug\b", r"\berror\b")),
]

_tfidf_vectorizer = None
_kb_tfidf_matrix = None
_kb_reference = None


def _init_tfidf(knowledge_base):
    global _tfidf_vectorizer, _kb_tfidf_matrix, _kb_reference
    if _tfidf_vectorizer is None:
        _tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        _kb_tfidf_matrix = _tfidf_vectorizer.fit_transform(
            knowledge_base["customer_message"].astype(str)
        )
        _kb_reference = knowledge_base.reset_index(drop=True)


def tfidf_nearest_reply(text, knowledge_base):
    _init_tfidf(knowledge_base)
    query_vector = _tfidf_vectorizer.transform([text])
    similarities = cosine_similarity(query_vector, _kb_tfidf_matrix)[0]
    best_index = int(np.argmax(similarities))
    return _kb_reference.iloc[best_index]["brand_reply"], float(similarities[best_index])

def simple_predict(text, thread_context="", knowledge_base=None):
    text_lower = str(text).lower()
    intent = "Other"
    for label, patterns in KEYWORD_RULES:
        if any(re.search(pattern, text_lower) for pattern in patterns):
            intent = label
            break

    escalate = intent == "Billing/Subscription" and ("refund" in text_lower or "$" in text_lower)

    reply = "Thanks for letting us know, we'll look into this."
    if knowledge_base is not None and len(knowledge_base) > 0:
        reply, _similarity_score = tfidf_nearest_reply(text, knowledge_base)

    return {
        "intent": intent,
        "reply": reply,
        "escalate": escalate,
        "escalate_reason": "Contains refund/dollar language" if escalate else "No trigger keywords matched"
    }


def offline_predict(text, thread_context="", knowledge_base=None):
    return simple_predict(text, thread_context, knowledge_base)